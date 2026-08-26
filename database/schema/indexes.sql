-- VIGYAN Campus Database Architecture - Indexes
-- Optimizes query paths for agent lookups, room matching, faculty search, registration ranges, and live queries

-- Faculty Indexes
CREATE INDEX IF NOT EXISTS idx_faculty_full_name ON faculty(full_name);
CREATE INDEX IF NOT EXISTS idx_faculty_department_id ON faculty(department_id);
CREATE INDEX IF NOT EXISTS idx_faculty_email ON faculty(email);
CREATE INDEX IF NOT EXISTS idx_faculty_room ON faculty(room);
CREATE INDEX IF NOT EXISTS idx_faculty_block ON faculty(block);

-- Departments Indexes
CREATE INDEX IF NOT EXISTS idx_departments_name ON departments(name);
CREATE INDEX IF NOT EXISTS idx_departments_short_name ON departments(short_name);

-- Subjects Indexes
CREATE INDEX IF NOT EXISTS idx_subjects_name ON subjects(name);
CREATE INDEX IF NOT EXISTS idx_subjects_code ON subjects(code);
CREATE INDEX IF NOT EXISTS idx_subjects_department_id ON subjects(department_id);

-- Faculty Subjects (Junction) Indexes
CREATE INDEX IF NOT EXISTS idx_faculty_subjects_subject_id ON faculty_subjects(subject_id);

-- Offices Indexes
CREATE INDEX IF NOT EXISTS idx_offices_name ON offices(name);
CREATE INDEX IF NOT EXISTS idx_offices_room ON offices(room);
CREATE INDEX IF NOT EXISTS idx_offices_block ON offices(block);

-- Counsellors Indexes
CREATE INDEX IF NOT EXISTS idx_counsellors_year ON counsellors(year);
CREATE INDEX IF NOT EXISTS idx_counsellors_section ON counsellors(section);
CREATE INDEX IF NOT EXISTS idx_counsellors_year_section ON counsellors(year, section);
CREATE INDEX IF NOT EXISTS idx_counsellors_reg_start ON counsellors(registration_range_start);
CREATE INDEX IF NOT EXISTS idx_counsellors_reg_end ON counsellors(registration_range_end);
CREATE INDEX IF NOT EXISTS idx_counsellors_faculty_id ON counsellors(faculty_id);

-- Academic Support Indexes
CREATE INDEX IF NOT EXISTS idx_academic_support_role_name ON academic_support(role_name);
CREATE INDEX IF NOT EXISTS idx_academic_support_person_name ON academic_support(person_name);
CREATE INDEX IF NOT EXISTS idx_academic_support_faculty_id ON academic_support(faculty_id);
CREATE INDEX IF NOT EXISTS idx_academic_support_office_id ON academic_support(office_id);

-- Locations Indexes
CREATE INDEX IF NOT EXISTS idx_locations_name ON locations(name);
CREATE INDEX IF NOT EXISTS idx_locations_type ON locations(location_type);
CREATE INDEX IF NOT EXISTS idx_locations_block ON locations(block);
CREATE INDEX IF NOT EXISTS idx_locations_room ON locations(room);
CREATE INDEX IF NOT EXISTS idx_locations_parent_id ON locations(parent_location_id);

-- Services Indexes
CREATE INDEX IF NOT EXISTS idx_services_name ON services(name);
CREATE INDEX IF NOT EXISTS idx_services_category ON services(category);
CREATE INDEX IF NOT EXISTS idx_services_location_id ON services(location_id);

-- Routes Indexes
CREATE INDEX IF NOT EXISTS idx_routes_start_location_id ON routes(start_location_id);
CREATE INDEX IF NOT EXISTS idx_routes_destination_location_id ON routes(destination_location_id);
CREATE INDEX IF NOT EXISTS idx_routes_start_dest ON routes(start_location_id, destination_location_id);

-- Live Status Indexes
CREATE INDEX IF NOT EXISTS idx_live_status_service_id ON live_status(service_id);
CREATE INDEX IF NOT EXISTS idx_live_status_status ON live_status(status);
CREATE INDEX IF NOT EXISTS idx_live_status_recorded_at ON live_status(recorded_at);
CREATE INDEX IF NOT EXISTS idx_live_status_expires_at ON live_status(expires_at);

-- Feedback Indexes
CREATE INDEX IF NOT EXISTS idx_feedback_tool_used ON feedback(tool_used);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);

-- Sources Indexes
CREATE INDEX IF NOT EXISTS idx_sources_source_type ON sources(source_type);
