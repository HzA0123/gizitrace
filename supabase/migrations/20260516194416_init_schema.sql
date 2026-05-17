-- ==========================================
-- GIZITRACE: INITIAL SCHEMA MIGRATION
-- ==========================================

-- 1. Create custom enums
CREATE TYPE public.user_role_type AS ENUM ('staff', 'kepsek', 'dinas', 'vendor');
CREATE TYPE public.anomaly_type AS ENUM ('ghost_delivery', 'scan_spike', 'zero_waste', 'low_adoption', 'no_delivery');
CREATE TYPE public.severity_level AS ENUM ('low', 'medium', 'high');

-- 2. Create Tables
CREATE TABLE public.schools (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR NOT NULL,
  address TEXT NOT NULL,
  district VARCHAR NOT NULL,
  city VARCHAR NOT NULL,
  total_students INTEGER NOT NULL DEFAULT 0,
  qr_token VARCHAR UNIQUE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE public.classes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  school_id UUID NOT NULL REFERENCES public.schools(id) ON DELETE CASCADE,
  name VARCHAR NOT NULL,
  grade INTEGER NOT NULL,
  student_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE public.vendors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR NOT NULL,
  contact VARCHAR,
  assigned_schools UUID[] DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE public.deliveries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vendor_id UUID NOT NULL REFERENCES public.vendors(id) ON DELETE RESTRICT,
  school_id UUID NOT NULL REFERENCES public.schools(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  reported_portions INTEGER NOT NULL DEFAULT 0,
  menu_description TEXT NOT NULL,
  delivery_confirmed BOOLEAN NOT NULL DEFAULT false,
  confirmed_at TIMESTAMP WITH TIME ZONE,
  confirmed_by VARCHAR,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE public.feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  school_id UUID NOT NULL REFERENCES public.schools(id) ON DELETE CASCADE,
  class_id UUID NOT NULL REFERENCES public.classes(id) ON DELETE CASCADE,
  delivery_id UUID NOT NULL REFERENCES public.deliveries(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  response_full INTEGER NOT NULL DEFAULT 0,
  response_half INTEGER NOT NULL DEFAULT 0,
  response_reject INTEGER NOT NULL DEFAULT 0,
  total_responses INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE public.food_photos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  delivery_id UUID NOT NULL REFERENCES public.deliveries(id) ON DELETE CASCADE,
  school_id UUID NOT NULL REFERENCES public.schools(id) ON DELETE CASCADE,
  photo_url TEXT NOT NULL,
  ai_waste_percent FLOAT,
  ai_confidence FLOAT,
  processed_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
  fallback_manual BOOLEAN DEFAULT false
);

CREATE TABLE public.anomalies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  delivery_id UUID REFERENCES public.deliveries(id) ON DELETE CASCADE,
  school_id UUID NOT NULL REFERENCES public.schools(id) ON DELETE CASCADE,
  type public.anomaly_type NOT NULL,
  description TEXT,
  severity public.severity_level NOT NULL,
  is_resolved BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE public.menu_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  school_id UUID NOT NULL REFERENCES public.schools(id) ON DELETE CASCADE,
  menu_name VARCHAR NOT NULL,
  date DATE NOT NULL,
  acceptance_rate FLOAT,
  avg_waste_percent FLOAT,
  total_feedback INTEGER DEFAULT 0
);

CREATE TABLE public.user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role public.user_role_type NOT NULL,
    school_id UUID REFERENCES public.schools(id) ON DELETE CASCADE,
    vendor_id UUID REFERENCES public.vendors(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id)
);

-- ==========================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ==========================================

ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own role" ON public.user_roles FOR SELECT TO authenticated USING ( auth.uid() = user_id );

CREATE POLICY "Anon and Auth can view schools" ON public.schools FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Anon and Auth can view classes" ON public.classes FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Anon and Auth can view menu_history" ON public.menu_history FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY "Anon can insert feedback" ON public.feedback FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Auth can view vendors" ON public.vendors FOR SELECT TO authenticated USING (true);
CREATE POLICY "Auth can view feedback" ON public.feedback FOR SELECT TO authenticated USING (true);
CREATE POLICY "Auth can view deliveries" ON public.deliveries FOR SELECT TO authenticated USING (true);
CREATE POLICY "Auth can view food_photos" ON public.food_photos FOR SELECT TO authenticated USING (true);
CREATE POLICY "Auth can view anomalies" ON public.anomalies FOR SELECT TO authenticated USING (true);

CREATE POLICY "Users can insert deliveries" ON public.deliveries FOR INSERT TO authenticated
WITH CHECK (
    EXISTS (SELECT 1 FROM public.user_roles ur WHERE ur.user_id = auth.uid() AND (ur.school_id = school_id OR ur.vendor_id = vendor_id))
    OR EXISTS (SELECT 1 FROM public.user_roles ur WHERE ur.user_id = auth.uid() AND ur.role = 'dinas')
);

CREATE POLICY "Users can update deliveries" ON public.deliveries FOR UPDATE TO authenticated
USING (
    EXISTS (SELECT 1 FROM public.user_roles ur WHERE ur.user_id = auth.uid() AND (ur.school_id = school_id OR ur.vendor_id = vendor_id))
    OR EXISTS (SELECT 1 FROM public.user_roles ur WHERE ur.user_id = auth.uid() AND ur.role = 'dinas')
);

CREATE POLICY "Users can insert food_photos" ON public.food_photos FOR INSERT TO authenticated
WITH CHECK (
    EXISTS (SELECT 1 FROM public.user_roles ur WHERE ur.user_id = auth.uid() AND ur.school_id = school_id)
);

CREATE POLICY "Users can update anomalies" ON public.anomalies FOR UPDATE TO authenticated
USING (
    EXISTS (SELECT 1 FROM public.user_roles ur WHERE ur.user_id = auth.uid() AND ur.school_id = school_id)
    OR EXISTS (SELECT 1 FROM public.user_roles ur WHERE ur.user_id = auth.uid() AND ur.role = 'dinas')
);

-- ==========================================
-- STORAGE SETTINGS (food_photos bucket)
-- ==========================================

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES ('food_photos', 'food_photos', false, 5242880, ARRAY['image/jpeg', 'image/png', 'image/webp'])
ON CONFLICT (id) DO UPDATE SET 
  public = false, 
  file_size_limit = 5242880, 
  allowed_mime_types = ARRAY['image/jpeg', 'image/png', 'image/webp'];

-- Drop older policies from previous split migrations if they exist to keep it clean
DO $$
BEGIN
    DROP POLICY IF EXISTS "Public Access" ON storage.objects;
    DROP POLICY IF EXISTS "Public Insert" ON storage.objects;
    
    -- Allow Auth Insert for private bucket
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'objects' AND policyname = 'Auth Insert') THEN
        CREATE POLICY "Auth Insert" ON storage.objects FOR INSERT TO authenticated WITH CHECK ( bucket_id = 'food_photos' );
    END IF;
END $$;
