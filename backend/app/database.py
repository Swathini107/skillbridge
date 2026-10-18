import os
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skillbridge.db")

# Normalize Heroku / Supabase / Render postgres URL prefix for SQLAlchemy compatibility
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

from sqlalchemy.pool import QueuePool

is_sqlite = DATABASE_URL.startswith("sqlite")

engine_kwargs = {}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
    engine_kwargs["poolclass"] = QueuePool
    engine_kwargs["pool_size"] = 15
    engine_kwargs["max_overflow"] = 25
    engine_kwargs["pool_timeout"] = 30
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(DATABASE_URL, **engine_kwargs)

if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency function to get database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables, apply missing column migrations, and seed default user."""
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Perform safe column migrations & index creation for SQLite
    if is_sqlite:
        with engine.connect() as conn:
            try:
                # Performance Indexes for high-frequency queries
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_job_applications_created_at ON job_applications(created_at)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_job_applications_updated_at ON job_applications(updated_at)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_interview_questions_created_at ON interview_questions(created_at)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_job_analyses_created_at ON job_analyses(created_at)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_practice_sessions_created_at ON practice_sessions(created_at)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_practice_answers_order_index ON practice_answers(order_index)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_resumes_updated_at ON resumes(updated_at)"))
                conn.commit()

                # Check existing columns in job_applications
                result = conn.execute(text("PRAGMA table_info(job_applications)"))
                existing_columns = [row[1] for row in result.fetchall()]

                new_columns = [
                    ("company_url", "VARCHAR(500)"),
                    ("location", "VARCHAR(150)"),
                    ("work_mode", "VARCHAR(50)"),
                    ("employment_type", "VARCHAR(50)"),
                    ("skills", "TEXT"),
                    ("deadline", "DATE"),
                    ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
                ]

                for col_name, col_type in new_columns:
                    if col_name not in existing_columns:
                        conn.execute(text(f"ALTER TABLE job_applications ADD COLUMN {col_name} {col_type}"))
                        conn.commit()

                # Check existing columns in interview_questions
                q_result = conn.execute(text("PRAGMA table_info(interview_questions)"))
                existing_q_cols = [row[1] for row in q_result.fetchall()]

                new_q_columns = [
                    ("round_type", "VARCHAR(50) DEFAULT 'Technical'"),
                    ("topic", "VARCHAR(100)"),
                    ("difficulty", "VARCHAR(50) DEFAULT 'Intermediate'"),
                    ("job_role", "VARCHAR(150)"),
                    ("job_id", "INTEGER REFERENCES job_applications(id) ON DELETE SET NULL"),
                    ("interview_date", "DATE"),
                    ("source", "VARCHAR(50) DEFAULT 'Personal interview'"),
                    ("original_answer", "TEXT"),
                    ("expected_answer", "TEXT"),
                    ("improvement_notes", "TEXT"),
                    ("tags", "TEXT"),
                    ("review_status", "VARCHAR(50) DEFAULT 'New'"),
                    ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
                ]

                for col_name, col_type in new_q_columns:
                    if col_name not in existing_q_cols:
                        conn.execute(text(f"ALTER TABLE interview_questions ADD COLUMN {col_name} {col_type}"))
                        conn.commit()

            except Exception:
                pass

    # Ensure default demo user exists using ORM (engine-agnostic)
    try:
        with SessionLocal() as session:
            demo_user = session.query(models.User).filter_by(id=1).first()
            if not demo_user:
                demo_user = models.User(id=1, name="Student Demo", email="student@skillbridge.edu")
                session.add(demo_user)
                session.commit()
    except Exception:
        pass
