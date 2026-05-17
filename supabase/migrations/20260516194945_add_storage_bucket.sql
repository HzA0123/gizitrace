-- Create the storage bucket for food_photos if it doesn't exist
INSERT INTO storage.buckets (id, name, public)
VALUES ('food_photos', 'food_photos', true)
ON CONFLICT (id) DO NOTHING;

-- RLS on storage.objects is already enabled by default by Supabase.
DO $$
BEGIN
    -- Allow public access to view photos
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'objects' AND policyname = 'Public Access'
    ) THEN
        CREATE POLICY "Public Access"
        ON storage.objects FOR SELECT
        USING ( bucket_id = 'food_photos' );
    END IF;

    -- Allow public insert (since it's an MVP)
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'objects' AND policyname = 'Public Insert'
    ) THEN
        CREATE POLICY "Public Insert"
        ON storage.objects FOR INSERT
        WITH CHECK ( bucket_id = 'food_photos' );
    END IF;
END $$;
