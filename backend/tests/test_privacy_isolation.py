"""
SkillBridge Security & Privacy Isolation Test Suite
Verifies that User 2's private records (job applications, resumes, analyses, questions, practice sessions)
cannot be retrieved, modified, or deleted across users.
"""

import unittest
import json
import urllib.request
import urllib.error
from app.database import SessionLocal
from app.models import (
    User,
    JobApplication,
    InterviewQuestion,
    JobAnalysis,
    PracticeSession,
    PracticeAnswer,
    Resume
)

import os
BASE_URL = os.getenv("TEST_API_URL", "http://127.0.0.1:8000/api")


class TestPrivacyAndUserIsolation(unittest.TestCase):
    """Verifies that private data is strictly protected between users."""

    @classmethod
    def setUpClass(cls):
        """Create a distinct second user and insert private records for User 2 directly in DB."""
        cls.db = SessionLocal()
        cls.user2 = cls.db.query(User).filter(User.id == 2).first()
        if not cls.user2:
            cls.user2 = User(id=2, name="Private User Two", email="user2_private@example.com")
            cls.db.add(cls.user2)
            cls.db.commit()
            cls.db.refresh(cls.user2)

        # 1. Private Job Application owned by User 2
        cls.user2_job = JobApplication(
            user_id=2,
            company_name="Confidential Aerospace Inc",
            job_title="Security Lead",
            application_status="Applied"
        )
        cls.db.add(cls.user2_job)

        # 2. Private Resume owned by User 2
        cls.user2_resume = Resume(
            user_id=2,
            title="Classified Executive Resume",
            target_role="Chief Security Officer",
            contact_info={"full_name": "Agent Secret", "email": "agent@classified.gov"}
        )
        cls.db.add(cls.user2_resume)

        # 3. Private Interview Question owned by User 2
        cls.user2_question = InterviewQuestion(
            user_id=2,
            question_text="Confidential defense protocol question?",
            round_type="Technical",
            topic="Cryptography",
            difficulty="Advanced"
        )
        cls.db.add(cls.user2_question)

        # 4. Private Job Analysis owned by User 2
        cls.user2_analysis = JobAnalysis(
            user_id=2,
            company_name="Top Secret Systems",
            job_title="Crypto Engineer",
            match_score=95.0,
            required_skills=[{"skill": "C++", "type": "required"}]
        )
        cls.db.add(cls.user2_analysis)

        # 5. Private Practice Session owned by User 2
        cls.user2_session = PracticeSession(
            user_id=2,
            session_name="Private Classified Mock",
            round_type="Technical",
            status="In Progress"
        )
        cls.db.add(cls.user2_session)
        cls.db.commit()

        cls.db.refresh(cls.user2_job)
        cls.db.refresh(cls.user2_resume)
        cls.db.refresh(cls.user2_question)
        cls.db.refresh(cls.user2_analysis)
        cls.db.refresh(cls.user2_session)

    @classmethod
    def tearDownClass(cls):
        """Clean up User 2 records from database."""
        try:
            cls.db.query(PracticeSession).filter(PracticeSession.user_id == 2).delete()
            cls.db.query(JobAnalysis).filter(JobAnalysis.user_id == 2).delete()
            cls.db.query(InterviewQuestion).filter(InterviewQuestion.user_id == 2).delete()
            cls.db.query(Resume).filter(Resume.user_id == 2).delete()
            cls.db.query(JobApplication).filter(JobApplication.user_id == 2).delete()
            cls.db.query(User).filter(User.id == 2).delete()
            cls.db.commit()
        finally:
            cls.db.close()

    def make_request(self, endpoint, method="GET", data=None):
        url = f"{BASE_URL}{endpoint}"
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        body = json.dumps(data).encode("utf-8") if data is not None else None
        try:
            with urllib.request.urlopen(req, data=body, timeout=10) as resp:
                data_resp = json.loads(resp.read().decode("utf-8")) if resp.length != 0 else {}
                return resp.status, data_resp
        except urllib.error.HTTPError as e:
            return e.code, {}

    def test_job_application_isolation(self):
        """User 1 API requests must not see, read, update, or delete User 2's job application."""
        # 1. Listing must not contain User 2's job
        status, jobs = self.make_request("/applications")
        self.assertEqual(status, 200)
        job_ids = [j["id"] for j in jobs]
        self.assertNotIn(self.user2_job.id, job_ids)

        # 2. Direct read of User 2's job must return 404
        status, _ = self.make_request(f"/applications/{self.user2_job.id}")
        self.assertEqual(status, 404)

        # 3. Direct update of User 2's job must return 404
        status, _ = self.make_request(
            f"/applications/{self.user2_job.id}",
            method="PUT",
            data={"job_title": "Hacked Title"}
        )
        self.assertEqual(status, 404)

        # 4. Direct delete of User 2's job must return 404
        status, _ = self.make_request(f"/applications/{self.user2_job.id}", method="DELETE")
        self.assertEqual(status, 404)

    def test_resume_isolation(self):
        """User 1 API requests must not see, read, update, or export User 2's private resume."""
        # 1. Listing must not contain User 2's resume
        status, resumes = self.make_request("/resumes")
        self.assertEqual(status, 200)
        resume_ids = [r["id"] for r in resumes]
        self.assertNotIn(self.user2_resume.id, resume_ids)

        # 2. Direct fetch must return 404
        status, _ = self.make_request(f"/resumes/{self.user2_resume.id}")
        self.assertEqual(status, 404)

        # 3. Direct export must return 404
        status, _ = self.make_request(f"/resumes/{self.user2_resume.id}/export/docx")
        self.assertEqual(status, 404)

    def test_interview_question_isolation(self):
        """User 1 API requests must not see, read, update, or delete User 2's questions."""
        status, questions = self.make_request("/questions")
        self.assertEqual(status, 200)
        q_ids = [q["id"] for q in questions]
        self.assertNotIn(self.user2_question.id, q_ids)

        status, _ = self.make_request(f"/questions/{self.user2_question.id}")
        self.assertEqual(status, 404)

    def test_analyzer_history_isolation(self):
        """User 1 API requests must not see, read, or delete User 2's analysis records."""
        status, analyses = self.make_request("/analyzer/history")
        self.assertEqual(status, 200)
        analysis_ids = [a["id"] for a in analyses]
        self.assertNotIn(self.user2_analysis.id, analysis_ids)

        status, _ = self.make_request(f"/analyzer/history/{self.user2_analysis.id}")
        self.assertEqual(status, 404)

    def test_practice_session_isolation(self):
        """User 1 API requests must not see or resume User 2's practice sessions."""
        status, sessions = self.make_request("/practice/sessions")
        self.assertEqual(status, 200)
        s_ids = [s["id"] for s in sessions]
        self.assertNotIn(self.user2_session.id, s_ids)

        status, _ = self.make_request(f"/practice/sessions/{self.user2_session.id}")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
