-- SkillBridge Database Schema (SQLite compatible)
-- Day 2: Job Saver & Application Tracker Enhanced Schema

PRAGMA foreign_keys = ON;

-- 1. Users Table
-- Stores student profile information
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Job Applications Table
-- Stores job postings, applied status, logistics, and interview tracking
-- Status Options:
--   - 'Saved': Job opportunity saved for review / yet to apply
--   - 'Applied': Application officially submitted
--   - 'Assessment': Online assessment or technical test stage
--   - 'Interview': Active interview stage (screening, technical, behavioral)
--   - 'Offer': Job offer extended
--   - 'Rejected': Application not moving forward
--   - 'Withdrawn': Application withdrawn by student
-- Work Mode Options:
--   - 'On-site', 'Hybrid', 'Remote'
-- Employment Type Options:
--   - 'Internship', 'Full-time', 'Part-time'
CREATE TABLE IF NOT EXISTS job_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_name TEXT NOT NULL,
    job_title TEXT NOT NULL,
    application_status TEXT DEFAULT 'Saved' CHECK(
        application_status IN ('Saved', 'Applied', 'Assessment', 'Interview', 'Offer', 'Rejected', 'Withdrawn')
    ),
    job_description TEXT,
    job_url TEXT,
    company_url TEXT,
    location TEXT,
    work_mode TEXT CHECK(work_mode IN ('On-site', 'Hybrid', 'Remote', NULL)),
    employment_type TEXT CHECK(employment_type IN ('Internship', 'Full-time', 'Part-time', NULL)),
    skills TEXT,
    deadline DATE,
    application_date DATE,
    interview_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Interview Questions Table (Day 4: Interview Memory Bank)
-- Stores real questions encountered by students, original answers, improvement notes, and review status
CREATE TABLE IF NOT EXISTS interview_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    job_id INTEGER,
    question_text TEXT NOT NULL,
    round_type TEXT DEFAULT 'Technical' CHECK(
        round_type IN ('Technical', 'HR', 'Aptitude', 'Behavioral', 'System Design')
    ),
    topic TEXT,
    difficulty TEXT DEFAULT 'Intermediate' CHECK(
        difficulty IN ('Beginner', 'Intermediate', 'Advanced')
    ),
    company_name TEXT,
    job_role TEXT,
    interview_date DATE,
    source TEXT DEFAULT 'Personal interview' CHECK(
        source IN ('Personal interview', 'Recruiter', 'Online assessment', 'Peer', 'Other')
    ),
    original_answer TEXT,
    expected_answer TEXT,
    improvement_notes TEXT,
    tags TEXT,
    review_status TEXT DEFAULT 'New' CHECK(
        review_status IN ('New', 'Learning', 'Confident')
    ),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Legacy compatibility columns
    job_title TEXT,
    personal_answer TEXT,
    question_category TEXT,
    interview_round TEXT,
    practice_status TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES job_applications(id) ON DELETE SET NULL
);

-- Indices for performance on lookups, filtering, and sorting
CREATE INDEX IF NOT EXISTS idx_job_applications_user_id ON job_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_status ON job_applications(application_status);
CREATE INDEX IF NOT EXISTS idx_job_applications_company ON job_applications(company_name);
CREATE INDEX IF NOT EXISTS idx_job_applications_title ON job_applications(job_title);
CREATE INDEX IF NOT EXISTS idx_job_applications_work_mode ON job_applications(work_mode);
CREATE INDEX IF NOT EXISTS idx_job_applications_emp_type ON job_applications(employment_type);
CREATE INDEX IF NOT EXISTS idx_job_applications_deadline ON job_applications(deadline);

CREATE INDEX IF NOT EXISTS idx_interview_questions_user_id ON interview_questions(user_id);
CREATE INDEX IF NOT EXISTS idx_interview_questions_round ON interview_questions(round_type);
CREATE INDEX IF NOT EXISTS idx_interview_questions_status ON interview_questions(review_status);
CREATE INDEX IF NOT EXISTS idx_interview_questions_difficulty ON interview_questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_interview_questions_company ON interview_questions(company_name);
CREATE INDEX IF NOT EXISTS idx_interview_questions_topic ON interview_questions(topic);
CREATE INDEX IF NOT EXISTS idx_interview_questions_job_id ON interview_questions(job_id);

-- 4. Job Analyses Table (Day 3 Feature)
-- Stores persistent job description analysis history, score breakdowns, and skill gaps
CREATE TABLE IF NOT EXISTS job_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    job_id INTEGER,
    company_name TEXT,
    job_title TEXT,
    match_score REAL,
    required_skills JSON,
    preferred_skills JSON,
    unclassified_skills JSON,
    other_requirements JSON,
    matching_skills JSON,
    missing_skills JSON,
    score_breakdown JSON,
    recommendations JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES job_applications(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_job_analyses_user_id ON job_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_job_analyses_job_id ON job_analyses(job_id);
CREATE INDEX IF NOT EXISTS idx_job_analyses_created_at ON job_analyses(created_at);

-- 5. Practice Sessions Table (Day 5: Mock Interview Practice Studio)
-- Stores setup parameters, time limits, duration, status, and progress for mock interviews
CREATE TABLE IF NOT EXISTS practice_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    job_id INTEGER,
    session_name TEXT NOT NULL,
    target_company TEXT,
    target_role TEXT,
    round_type TEXT DEFAULT 'Technical' CHECK(
        round_type IN ('Technical', 'HR', 'Aptitude', 'Behavioral', 'System Design')
    ),
    question_source TEXT DEFAULT 'Memory Bank',
    selected_topic TEXT,
    difficulty TEXT DEFAULT 'Mixed' CHECK(
        difficulty IN ('Beginner', 'Intermediate', 'Advanced', 'Mixed')
    ),
    time_limit_minutes INTEGER,
    status TEXT DEFAULT 'In Progress' CHECK(
        status IN ('In Progress', 'Completed', 'Abandoned')
    ),
    total_questions INTEGER DEFAULT 0,
    current_question_index INTEGER DEFAULT 0,
    duration_seconds INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES job_applications(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_practice_sessions_user_id ON practice_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_practice_sessions_job_id ON practice_sessions(job_id);
CREATE INDEX IF NOT EXISTS idx_practice_sessions_status ON practice_sessions(status);
CREATE INDEX IF NOT EXISTS idx_practice_sessions_round ON practice_sessions(round_type);
CREATE INDEX IF NOT EXISTS idx_practice_sessions_created ON practice_sessions(created_at);

-- 6. Practice Answers Table (Day 5: Mock Interview Practice Studio)
-- Stores question snapshots, student responses, self-assessment criteria ratings, and reflections
CREATE TABLE IF NOT EXISTS practice_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    question_id INTEGER,
    order_index INTEGER DEFAULT 0 NOT NULL,
    question_text TEXT NOT NULL,
    round_type TEXT NOT NULL,
    topic TEXT,
    difficulty TEXT NOT NULL,
    expected_answer TEXT,
    answer_text TEXT,
    is_attempted BOOLEAN DEFAULT 0 NOT NULL,
    is_skipped BOOLEAN DEFAULT 0 NOT NULL,
    self_ratings JSON,
    went_well TEXT,
    was_difficult TEXT,
    need_to_learn TEXT,
    better_approach TEXT,
    time_spent_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES practice_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES interview_questions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_practice_answers_session_id ON practice_answers(session_id);
CREATE INDEX IF NOT EXISTS idx_practice_answers_question_id ON practice_answers(question_id);
CREATE INDEX IF NOT EXISTS idx_practice_answers_order ON practice_answers(session_id, order_index);
