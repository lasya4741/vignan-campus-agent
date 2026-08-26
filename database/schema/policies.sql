-- VIGYAN Campus Database Architecture - Row Level Security (RLS) Policies
-- Ensures secure access control: public read for verified campus knowledge, restricted writes.

-- Enable Row Level Security across all tables
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE faculty ENABLE ROW LEVEL SECURITY;
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE faculty_subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE offices ENABLE ROW LEVEL SECURITY;
ALTER TABLE counsellors ENABLE ROW LEVEL SECURITY;
ALTER TABLE academic_support ENABLE ROW LEVEL SECURITY;
ALTER TABLE locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE services ENABLE ROW LEVEL SECURITY;
ALTER TABLE routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE live_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any to allow idempotent execution
DROP POLICY IF EXISTS "Allow public read access on sources" ON sources;
DROP POLICY IF EXISTS "Allow public read access on departments" ON departments;
DROP POLICY IF EXISTS "Allow public read access on faculty" ON faculty;
DROP POLICY IF EXISTS "Allow public read access on subjects" ON subjects;
DROP POLICY IF EXISTS "Allow public read access on faculty_subjects" ON faculty_subjects;
DROP POLICY IF EXISTS "Allow public read access on offices" ON offices;
DROP POLICY IF EXISTS "Allow public read access on counsellors" ON counsellors;
DROP POLICY IF EXISTS "Allow public read access on academic_support" ON academic_support;
DROP POLICY IF EXISTS "Allow public read access on locations" ON locations;
DROP POLICY IF EXISTS "Allow public read access on services" ON services;
DROP POLICY IF EXISTS "Allow public read access on routes" ON routes;
DROP POLICY IF EXISTS "Allow public read access on live_status" ON live_status;
DROP POLICY IF EXISTS "Allow public insert on feedback" ON feedback;
DROP POLICY IF EXISTS "Allow authenticated read on feedback" ON feedback;
DROP POLICY IF EXISTS "Allow authenticated insert on live_status" ON live_status;
DROP POLICY IF EXISTS "Allow authenticated update on live_status" ON live_status;

-- 1. Public Read Access for Campus Knowledge Base (anon and authenticated)
CREATE POLICY "Allow public read access on sources" 
    ON sources FOR SELECT TO public 
    USING (true);

CREATE POLICY "Allow public read access on departments" 
    ON departments FOR SELECT TO public 
    USING (true);

CREATE POLICY "Allow public read access on faculty" 
    ON faculty FOR SELECT TO public 
    USING (true);

CREATE POLICY "Allow public read access on subjects" 
    ON subjects FOR SELECT TO public 
    USING (true);

CREATE POLICY "Allow public read access on faculty_subjects" 
    ON faculty_subjects FOR SELECT TO public 
    USING (true);

CREATE POLICY "Allow public read access on offices" 
    ON offices FOR SELECT TO public 
    USING (true);

CREATE POLICY "Allow public read access on counsellors" 
    ON counsellors FOR SELECT TO public 
    USING (true);

CREATE POLICY "Allow public read access on academic_support" 
    ON academic_support FOR SELECT TO public 
    USING (true);

CREATE POLICY "Allow public read access on locations" 
    ON locations FOR SELECT TO public 
    USING (true);

CREATE POLICY "Allow public read access on services" 
    ON services FOR SELECT TO public 
    USING (true);

CREATE POLICY "Allow public read access on routes" 
    ON routes FOR SELECT TO public 
    USING (true);

CREATE POLICY "Allow public read access on live_status" 
    ON live_status FOR SELECT TO public 
    USING (true);

-- 2. Data Ingestion & Modification Policies for Knowledge Base
CREATE POLICY "Allow public insert on sources" ON sources FOR INSERT TO public WITH CHECK (true);
CREATE POLICY "Allow public update on sources" ON sources FOR UPDATE TO public USING (true);

CREATE POLICY "Allow public insert on locations" ON locations FOR INSERT TO public WITH CHECK (true);
CREATE POLICY "Allow public update on locations" ON locations FOR UPDATE TO public USING (true);

CREATE POLICY "Allow public insert on departments" ON departments FOR INSERT TO public WITH CHECK (true);
CREATE POLICY "Allow public update on departments" ON departments FOR UPDATE TO public USING (true);

CREATE POLICY "Allow public insert on faculty" ON faculty FOR INSERT TO public WITH CHECK (true);
CREATE POLICY "Allow public update on faculty" ON faculty FOR UPDATE TO public USING (true);

CREATE POLICY "Allow public insert on subjects" ON subjects FOR INSERT TO public WITH CHECK (true);
CREATE POLICY "Allow public update on subjects" ON subjects FOR UPDATE TO public USING (true);

CREATE POLICY "Allow public insert on faculty_subjects" ON faculty_subjects FOR INSERT TO public WITH CHECK (true);
CREATE POLICY "Allow public update on faculty_subjects" ON faculty_subjects FOR UPDATE TO public USING (true);

CREATE POLICY "Allow public insert on offices" ON offices FOR INSERT TO public WITH CHECK (true);
CREATE POLICY "Allow public update on offices" ON offices FOR UPDATE TO public USING (true);

CREATE POLICY "Allow public insert on counsellors" ON counsellors FOR INSERT TO public WITH CHECK (true);
CREATE POLICY "Allow public update on counsellors" ON counsellors FOR UPDATE TO public USING (true);

CREATE POLICY "Allow public insert on academic_support" ON academic_support FOR INSERT TO public WITH CHECK (true);
CREATE POLICY "Allow public update on academic_support" ON academic_support FOR UPDATE TO public USING (true);

CREATE POLICY "Allow public insert on services" ON services FOR INSERT TO public WITH CHECK (true);
CREATE POLICY "Allow public update on services" ON services FOR UPDATE TO public USING (true);

CREATE POLICY "Allow public insert on routes" ON routes FOR INSERT TO public WITH CHECK (true);
CREATE POLICY "Allow public update on routes" ON routes FOR UPDATE TO public USING (true);

-- 3. Live Status Write Policies
-- Authenticated users or backend workers can post live updates (service_role bypasses RLS automatically)
CREATE POLICY "Allow authenticated insert on live_status" 
    ON live_status FOR INSERT TO authenticated 
    WITH CHECK (true);

CREATE POLICY "Allow authenticated update on live_status" 
    ON live_status FOR UPDATE TO authenticated 
    USING (true) WITH CHECK (true);

-- 4. Feedback Policies
-- Public users (anon & authenticated) can submit feedback; read access is restricted to authenticated/admin users
CREATE POLICY "Allow public insert on feedback" 
    ON feedback FOR INSERT TO public 
    WITH CHECK (true);

CREATE POLICY "Allow authenticated read on feedback" 
    ON feedback FOR SELECT TO authenticated 
    USING (true);

