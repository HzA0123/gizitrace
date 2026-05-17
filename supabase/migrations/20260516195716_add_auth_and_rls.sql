-- Create ENUM for roles
CREATE TYPE public.user_role_type AS ENUM ('staff', 'kepsek', 'dinas', 'vendor');

-- Create user_roles table
CREATE TABLE public.user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role public.user_role_type NOT NULL,
    school_id UUID REFERENCES public.schools(id) ON DELETE CASCADE,
    vendor_id UUID REFERENCES public.vendors(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id)
);

-- Enable RLS on user_roles
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

-- RLS Policy for user_roles
CREATE POLICY "Users can read own role" 
ON public.user_roles FOR SELECT 
TO authenticated
USING ( auth.uid() = user_id );

-- (Note: INSERT/UPDATE for user_roles will be handled securely by the backend via Service Role)

-------------------------------------------------------------------------------
-- RLS POLICIES FOR EXISTING TABLES
-------------------------------------------------------------------------------

-- 1. PUBLIC / ANON ACCESS (Siswa)
-- Memperbolehkan siswa (tanpa login) membaca data untuk dirender di halaman QR
CREATE POLICY "Anon and Auth can view schools" ON public.schools FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Anon and Auth can view classes" ON public.classes FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Anon and Auth can view menu_history" ON public.menu_history FOR SELECT TO anon, authenticated USING (true);

-- Siswa bisa insert feedback
CREATE POLICY "Anon can insert feedback" ON public.feedback FOR INSERT TO anon
WITH CHECK (true);

-- 2. AUTHENTICATED ACCESS
-- Vendors (hanya butuh select)
CREATE POLICY "Auth can view vendors" ON public.vendors FOR SELECT TO authenticated USING (true);

-- Feedback
CREATE POLICY "Auth can view feedback" ON public.feedback FOR SELECT TO authenticated USING (true);

-- Deliveries
CREATE POLICY "Auth can view deliveries" ON public.deliveries FOR SELECT TO authenticated USING (true);

-- Food Photos
CREATE POLICY "Auth can view food_photos" ON public.food_photos FOR SELECT TO authenticated USING (true);

-- Anomalies
CREATE POLICY "Auth can view anomalies" ON public.anomalies FOR SELECT TO authenticated USING (true);

-- Insert & Update Policies for Authenticated Users (Staff/Kepsek/Vendor/Dinas)
-- Deliveries: Hanya bisa diubah oleh vendor yang bersangkutan atau staff sekolah yang bersangkutan
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

-- Food Photos: Bisa di-insert oleh staff sekolah tersebut
CREATE POLICY "Users can insert food_photos" ON public.food_photos FOR INSERT TO authenticated
WITH CHECK (
    EXISTS (SELECT 1 FROM public.user_roles ur WHERE ur.user_id = auth.uid() AND ur.school_id = school_id)
);

-- Anomalies: Bisa diedit/di-resolve oleh staff/kepsek/dinas
CREATE POLICY "Users can update anomalies" ON public.anomalies FOR UPDATE TO authenticated
USING (
    EXISTS (SELECT 1 FROM public.user_roles ur WHERE ur.user_id = auth.uid() AND ur.school_id = school_id)
    OR EXISTS (SELECT 1 FROM public.user_roles ur WHERE ur.user_id = auth.uid() AND ur.role = 'dinas')
);
