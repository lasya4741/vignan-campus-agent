# VIGYAN Campus Database Architecture

This directory contains the database design, schema definitions, indexes, Row Level Security (RLS) policies, seed templates, and provenance extraction structures for the **Vignan Campus AI Agent** system.

---

## 1. Directory Structure

```
database/
├── schema/
│   ├── schema.sql           # Core tables, constraints, foreign keys, triggers
│   ├── indexes.sql          # High-performance search & lookup indexes
│   └── policies.sql         # Supabase Row Level Security (RLS) policies
├── seeds/                   # Seed templates for importing verified campus records
│   ├── academic_support.sql
│   ├── counsellors.sql
│   ├── departments.sql
│   ├── faculty.sql
│   ├── live_status.sql
│   ├── locations.sql
│   ├── offices.sql
│   ├── routes.sql
│   ├── services.sql
│   ├── sources.sql
│   └── subjects.sql
├── raw/                     # Original raw source materials
│   ├── posters/             # Physical poster photos and notice board captures
│   └── source_notes/        # Manual field verification logs & handbook notes
├── extracted/               # Structured JSON extracts ready for ingestion
│   ├── academic_support.json
│   ├── counsellors.json
│   ├── departments.json
│   ├── faculty.json
│   ├── locations.json
│   ├── offices.json
│   ├── routes.json
│   ├── services.json
│   ├── sources.json
│   └── subjects.json
└── README.md
```

---

## 2. Database Tables Overview

| Table | Purpose | Primary Key | Key Foreign Keys / Relations |
| :--- | :--- | :--- | :--- |
| `sources` | Source provenance & verification metadata | `id` (UUID) | Root provenance record |
| `departments` | Academic & administrative departments | `id` (UUID) | `hod_faculty_id` -> `faculty`, `source_id` -> `sources` |
| `faculty` | Faculty directory with room, block, contact | `id` (UUID) | `department_id` -> `departments`, `source_id` -> `sources` |
| `subjects` | Courses and syllabus subjects | `id` (UUID) | `department_id` -> `departments`, `source_id` -> `sources` |
| `faculty_subjects` | Many-to-many junction between faculty & courses | `(faculty_id, subject_id)` | `faculty_id` -> `faculty`, `subject_id` -> `subjects` |
| `offices` | Campus administrative & student service offices | `id` (UUID) | `source_id` -> `sources` |
| `counsellors` | Student counsellor mapping (year/sec/reg range) | `id` (UUID) | `faculty_id` -> `faculty`, `source_id` -> `sources` |
| `academic_support` | Responsibility roles (placements, grievances, etc.) | `id` (UUID) | `faculty_id` -> `faculty`, `office_id` -> `offices` |
| `locations` | Physical campus hierarchy (gate, room, block) | `id` (UUID) | `parent_location_id` -> `locations`, `source_id` -> `sources` |
| `services` | Utilities (xerox, canteen, printing, library) | `id` (UUID) | `location_id` -> `locations`, `source_id` -> `sources` |
| `routes` | Deterministic step-by-step navigation paths | `id` (UUID) | `start_location_id` -> `locations`, `dest_location_id` -> `locations` |
| `live_status` | Dynamic queue lengths and wait times | `id` (UUID) | `service_id` -> `services` |
| `feedback` | Agent query feedback & rating metrics | `id` (UUID) | Standalone quality feedback loop |

---

## 3. Data Integrity & Provenance Principles

- **No Fabricated Records**: The database starts clean. Real campus data is populated strictly from verified handbooks, official circulars, and physically verified campus signage.
- **Source Tracking**: Every entity tracks `source_id`, `confidence` (`high`, `medium`, `low`, `needs_verification`), and `last_verified`.
- **Exact Room Identifiers**: Room numbers preserve exact sourced strings (e.g. `"409"`, `"NB-409"`) without destructive transformations.
- **Deterministic Navigation**: The AI agent utilizes recorded paths from `routes` rather than hallucinating navigation directions.

---

## 4. Security & Row Level Security (RLS)

- **Public Read Access**: Anonymous and authenticated users can read all verified campus knowledge tables (`sources`, `departments`, `faculty`, `subjects`, `offices`, `counsellors`, `academic_support`, `locations`, `services`, `routes`, `live_status`).
- **Controlled Writes**:
  - `feedback`: Public insertion (`anon` + `authenticated`); reading restricted to backend administrators.
  - `live_status`: Insertion & updates restricted to `authenticated` workers and `service_role`.
  - Core directory tables (`faculty`, `departments`, etc.): Restricted to `service_role` and administrative operations.
