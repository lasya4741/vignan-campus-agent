-- VIGYAN Campus Database Architecture - Core Schema
-- Schema version: 1.0.0
-- Target Engine: PostgreSQL 17 (Supabase)

-- Enable UUID generation extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- 1. SOURCES (Provenance & Source Verification System)
-- ============================================================================
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL CHECK (source_type IN (
        'official_website',
        'official_document',
        'department_verified',
        'campus_verified',
        'student_reported'
    )),
    source_name TEXT NOT NULL,
    source_url TEXT,
    description TEXT,
    document_name TEXT,
    collected_at TIMESTAMPTZ DEFAULT now(),
    verified_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- 2. DEPARTMENTS
-- ============================================================================
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    short_name TEXT,
    description TEXT,
    block TEXT,
    floor_information TEXT,
    hod_faculty_id UUID, -- Foreign key to faculty(id) added after faculty table creation
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    confidence TEXT DEFAULT 'high' CHECK (confidence IN ('high', 'medium', 'low', 'needs_verification')),
    last_verified TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- 3. FACULTY
-- ============================================================================
CREATE TABLE IF NOT EXISTS faculty (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    designation TEXT,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    email TEXT,
    phone TEXT,
    room TEXT,
    block TEXT,
    floor TEXT,
    profile_url TEXT,
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    confidence TEXT DEFAULT 'high' CHECK (confidence IN ('high', 'medium', 'low', 'needs_verification')),
    last_verified TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Add foreign key constraint from departments.hod_faculty_id to faculty.id
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_departments_hod_faculty'
    ) THEN
        ALTER TABLE departments 
        ADD CONSTRAINT fk_departments_hod_faculty 
        FOREIGN KEY (hod_faculty_id) REFERENCES faculty(id) ON DELETE SET NULL;
    END IF;
END $$;

-- ============================================================================
-- 4. SUBJECTS
-- ============================================================================
CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    code TEXT,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    confidence TEXT DEFAULT 'high' CHECK (confidence IN ('high', 'medium', 'low', 'needs_verification')),
    last_verified TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- 5. FACULTY_SUBJECTS (Many-to-Many Junction Table)
-- ============================================================================
CREATE TABLE IF NOT EXISTS faculty_subjects (
    faculty_id UUID NOT NULL REFERENCES faculty(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    confidence TEXT DEFAULT 'high' CHECK (confidence IN ('high', 'medium', 'low', 'needs_verification')),
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (faculty_id, subject_id)
);

-- ============================================================================
-- 6. OFFICES
-- ============================================================================
CREATE TABLE IF NOT EXISTS offices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    purpose TEXT,
    room TEXT,
    block TEXT,
    floor TEXT,
    phone TEXT,
    email TEXT,
    description TEXT,
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    confidence TEXT DEFAULT 'high' CHECK (confidence IN ('high', 'medium', 'low', 'needs_verification')),
    last_verified TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- 7. COUNSELLORS
-- ============================================================================
CREATE TABLE IF NOT EXISTS counsellors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_year TEXT,
    year INTEGER,
    section TEXT,
    counsellor_name TEXT NOT NULL,
    faculty_id UUID REFERENCES faculty(id) ON DELETE SET NULL,
    phone TEXT,
    room TEXT,
    registration_range_start TEXT,
    registration_range_end TEXT,
    registration_range_text TEXT,
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    confidence TEXT DEFAULT 'high' CHECK (confidence IN ('high', 'medium', 'low', 'needs_verification')),
    last_verified TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- 8. ACADEMIC SUPPORT (Responsibility-Based Roles)
-- ============================================================================
CREATE TABLE IF NOT EXISTS academic_support (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name TEXT NOT NULL,
    person_name TEXT NOT NULL,
    faculty_id UUID REFERENCES faculty(id) ON DELETE SET NULL,
    responsibilities TEXT,
    office_id UUID REFERENCES offices(id) ON DELETE SET NULL,
    room TEXT,
    phone TEXT,
    email TEXT,
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    confidence TEXT DEFAULT 'high' CHECK (confidence IN ('high', 'medium', 'low', 'needs_verification')),
    last_verified TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- 9. LOCATIONS
-- ============================================================================
CREATE TABLE IF NOT EXISTS locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    location_type TEXT NOT NULL CHECK (location_type IN (
        'gate',
        'building',
        'floor',
        'room',
        'office',
        'department',
        'service',
        'canteen',
        'facility',
        'other'
    )),
    block TEXT,
    floor TEXT,
    room TEXT,
    description TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    parent_location_id UUID REFERENCES locations(id) ON DELETE SET NULL,
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    confidence TEXT DEFAULT 'high' CHECK (confidence IN ('high', 'medium', 'low', 'needs_verification')),
    last_verified TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- 10. SERVICES
-- ============================================================================
CREATE TABLE IF NOT EXISTS services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'xerox',
        'printing',
        'stationery',
        'canteen',
        'transport',
        'medical',
        'library',
        'pharmacy',
        'other'
    )),
    description TEXT,
    location_id UUID REFERENCES locations(id) ON DELETE SET NULL,
    services_offered JSONB DEFAULT '[]'::jsonb,
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    confidence TEXT DEFAULT 'high' CHECK (confidence IN ('high', 'medium', 'low', 'needs_verification')),
    last_verified TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- 11. ROUTES (Deterministic Navigation Paths)
-- ============================================================================
CREATE TABLE IF NOT EXISTS routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    start_location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    destination_location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    estimated_minutes NUMERIC(5,2),
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    confidence TEXT DEFAULT 'high' CHECK (confidence IN ('high', 'medium', 'low', 'needs_verification')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- 12. LIVE STATUS (Dynamic / Real-Time Status)
-- ============================================================================
CREATE TABLE IF NOT EXISTS live_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('available', 'busy', 'full', 'closed', 'unknown')),
    queue_length INTEGER DEFAULT 0,
    estimated_wait_minutes INTEGER,
    reported_by TEXT,
    report_source TEXT,
    confidence TEXT DEFAULT 'high' CHECK (confidence IN ('high', 'medium', 'low', 'needs_verification')),
    recorded_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ
);

-- ============================================================================
-- 13. FEEDBACK (Recommendations & System Quality Loop)
-- ============================================================================
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_query TEXT,
    tool_used TEXT,
    recommendation TEXT,
    predicted_wait INTEGER,
    actual_wait INTEGER,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    feedback_type TEXT,
    feedback_text TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- Trigger Function: Auto-update updated_at
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach updated_at triggers
DROP TRIGGER IF EXISTS trg_sources_updated_at ON sources;
CREATE TRIGGER trg_sources_updated_at BEFORE UPDATE ON sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_departments_updated_at ON departments;
CREATE TRIGGER trg_departments_updated_at BEFORE UPDATE ON departments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_faculty_updated_at ON faculty;
CREATE TRIGGER trg_faculty_updated_at BEFORE UPDATE ON faculty FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_subjects_updated_at ON subjects;
CREATE TRIGGER trg_subjects_updated_at BEFORE UPDATE ON subjects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_offices_updated_at ON offices;
CREATE TRIGGER trg_offices_updated_at BEFORE UPDATE ON offices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_counsellors_updated_at ON counsellors;
CREATE TRIGGER trg_counsellors_updated_at BEFORE UPDATE ON counsellors FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_academic_support_updated_at ON academic_support;
CREATE TRIGGER trg_academic_support_updated_at BEFORE UPDATE ON academic_support FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_locations_updated_at ON locations;
CREATE TRIGGER trg_locations_updated_at BEFORE UPDATE ON locations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_services_updated_at ON services;
CREATE TRIGGER trg_services_updated_at BEFORE UPDATE ON services FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_routes_updated_at ON routes;
CREATE TRIGGER trg_routes_updated_at BEFORE UPDATE ON routes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
