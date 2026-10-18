"""
SkillBridge Days 6 & 7 Integration Test Suite
Complete Multi-Module End-to-End Workflow Verification:

1. Save a new Job Application (Day 2 Job Saver)
2. Run Job Description Analyzer with skill extraction & gap analysis (Day 3 Analyzer)
3. Save analysis to history and verify persistence
4. Save an Interview Question linked to the Job (Day 4 Memory Bank)
5. Filter questions by company and linked job ID
6. Start a Mock Practice Session targeting the Job (Day 5 Practice Studio)
7. Save answer, self-assessment ratings, and reflection
8. Finish practice session and verify transparent session report
9. Verify Dashboard summary reflects updated jobs, questions, and session metrics
10. Verify Non-Destructive Integrity (deleting sessions/analyses never deletes jobs/questions)
"""

import os
import unittest
import json
import urllib.request
import urllib.error

BASE_URL = os.getenv("TEST_API_URL", "http://127.0.0.1:8000/api")


class TestFullProductIntegrationWorkflow(unittest.TestCase):
    """End-to-end integration tests connecting all modules through real relational data."""

    def make_request(self, endpoint, method="GET", data=None):
        url = f"{BASE_URL}{endpoint}"
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
        try:
            with urllib.request.urlopen(req, data=encoded_data, timeout=10) as response:
                body = response.read().decode("utf-8")
                return response.status, json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            try:
                return e.code, json.loads(error_body)
            except Exception:
                return e.code, {"detail": error_body}

    def test_complete_student_career_journey(self):
        """Execute the complete multi-module workflow from job discovery to mock reflection."""

        # -------------------------------------------------------------
        # STEP 1: Check initial dashboard state
        # -------------------------------------------------------------
        status, initial_dashboard = self.make_request("/dashboard/summary")
        self.assertEqual(status, 200)
        init_cards = initial_dashboard["summary_cards"]
        initial_job_count = init_cards["total_jobs"]
        initial_q_count = init_cards["total_questions_saved"]
        initial_sess_count = init_cards["sessions_completed"]

        # -------------------------------------------------------------
        # STEP 2: Save a new job application (Day 2 Module)
        # -------------------------------------------------------------
        new_job_payload = {
            "company_name": "CloudScale Systems",
            "job_title": "Full Stack Software Engineer",
            "status": "Applied",
            "location": "Bengaluru, India",
            "work_mode": "Hybrid",
            "employment_type": "Full-time",
            "salary_range": "12 - 16 LPA",
            "job_url": "https://cloudscale.example.com/careers/fs-eng",
            "company_url": "https://cloudscale.example.com",
            "deadline": "2026-11-20",
            "notes": "Met campus recruiter during placement drive.",
            "skills": "React, Python, FastAPI, PostgreSQL, Docker, AWS"
        }
        status, created_job = self.make_request("/applications", method="POST", data=new_job_payload)
        self.assertEqual(status, 201)
        job_id = created_job["id"]
        self.assertIsNotNone(job_id)
        self.assertEqual(created_job["company_name"], "CloudScale Systems")

        # -------------------------------------------------------------
        # STEP 3: Analyze Job Description for this job (Day 3 Module)
        # -------------------------------------------------------------
        jd_text = """
        About CloudScale:
        We are building high-throughput distributed cloud services.
        Requirements:
        - Strong proficiency in Python, FastAPI, and PostgreSQL.
        - Experience with React, JavaScript, and HTML5 for frontend applications.
        - Understanding of Docker containerization and Git version control.
        Preferred:
        - Experience with Kubernetes and Redis caching.
        - Familiarity with CI/CD pipelines.
        """
        student_resume = """
        Student with strong foundations in Python, JavaScript, React, and Git.
        Built REST APIs using FastAPI and SQLite.
        Completed coursework in Relational Databases and Data Structures.
        """

        analysis_payload = {
            "job_id": job_id,
            "company_name": "CloudScale Systems",
            "job_title": "Full Stack Software Engineer",
            "job_description": jd_text,
            "resume_or_profile_text": student_resume,
            "save_analysis": True
        }
        status, analysis_res = self.make_request("/analyzer/analyze", method="POST", data=analysis_payload)
        self.assertEqual(status, 200)
        self.assertIn("match_score", analysis_res)
        self.assertIn("matching_required", analysis_res)
        self.assertIn("missing_required", analysis_res)
        self.assertIn("recommendations", analysis_res)
        self.assertGreater(len(analysis_res["recommendations"]), 0)

        analysis_id = analysis_res.get("id")
        self.assertIsNotNone(analysis_id)

        # Verify analysis history lists the new analysis
        status, history_list = self.make_request("/analyzer/history")
        self.assertEqual(status, 200)
        found_hist = next((h for h in history_list if h["id"] == analysis_id), None)
        self.assertIsNotNone(found_hist)
        self.assertEqual(found_hist["company_name"], "CloudScale Systems")

        # -------------------------------------------------------------
        # STEP 4: Save an Interview Question linked to the Job (Day 4 Module)
        # -------------------------------------------------------------
        question_payload = {
            "question_text": "How do database connection pools work in SQLAlchemy, and why is pool_pre_ping important?",
            "round_type": "Technical",
            "topic": "Databases & SQLAlchemy",
            "difficulty": "Intermediate",
            "job_id": job_id,
            "company_name": "CloudScale Systems",
            "job_role": "Full Stack Software Engineer",
            "original_answer": "Connection pools keep persistent DB connections open to prevent handshake overhead.",
            "expected_answer": "pool_pre_ping tests liveness with SELECT 1 before checkout, avoiding stale disconnected sockets.",
            "improvement_notes": "Mention pool_recycle and max_overflow parameters.",
            "tags": "python, sqlalchemy, databases, backend",
            "review_status": "Learning"
        }
        status, created_question = self.make_request("/questions", method="POST", data=question_payload)
        self.assertEqual(status, 201)
        question_id = created_question["id"]
        self.assertIsNotNone(question_id)
        self.assertEqual(created_question["job_id"], job_id)

        # Verify filtering questions by job_id
        status, filtered_questions = self.make_request(f"/questions?job_id={job_id}")
        self.assertEqual(status, 200)
        self.assertEqual(len(filtered_questions), 1)
        self.assertEqual(filtered_questions[0]["id"], question_id)

        # -------------------------------------------------------------
        # STEP 5: Start a Mock Interview Session targeting this Job (Day 5 Module)
        # -------------------------------------------------------------
        session_payload = {
            "session_name": "CloudScale Systems — Technical Interview Round",
            "round_type": "Technical",
            "job_id": job_id,
            "target_company": "CloudScale Systems",
            "target_role": "Full Stack Software Engineer",
            "question_source": "Memory Bank",
            "difficulty": "Mixed",
            "question_count": 3,
            "time_limit_minutes": 15
        }
        status, started_session = self.make_request("/practice/sessions", method="POST", data=session_payload)
        self.assertEqual(status, 201)
        session_id = started_session["id"]
        self.assertIsNotNone(session_id)
        self.assertEqual(started_session["status"], "In Progress")
        self.assertEqual(len(started_session["answers"]), 3)

        # Verify the session prioritized the question linked to this job
        session_question_texts = [ans["question_text"] for ans in started_session["answers"]]
        self.assertIn(
            "How do database connection pools work in SQLAlchemy, and why is pool_pre_ping important?",
            session_question_texts
        )

        # -------------------------------------------------------------
        # STEP 6: Save answer, ratings, and reflection in practice session
        # -------------------------------------------------------------
        first_answer = started_session["answers"][0]
        answer_id = first_answer["id"]
        answer_update_payload = {
            "answer_text": "A connection pool maintains a pool of active database connections to avoid TCP handshake costs.",
            "time_spent_seconds": 95,
            "self_ratings": {
                "technical_accuracy": 5,
                "clarity": 4,
                "confidence": 4
            },
            "went_well": "Clear explanation of pool reuse benefits.",
            "was_difficult": "Explaining max_overflow vs pool_size.",
            "need_to_learn": "Read SQLAlchemy engine documentation on pooling strategies.",
            "better_approach": "Mention connection recycling to avoid firewall timeouts.",
            "is_skipped": False
        }
        status, updated_answer = self.make_request(
            f"/practice/sessions/{session_id}/answers/{answer_id}",
            method="PUT",
            data=answer_update_payload
        )
        self.assertEqual(status, 200)
        self.assertTrue(updated_answer["is_attempted"])

        # -------------------------------------------------------------
        # STEP 7: Complete the Practice Session and inspect report
        # -------------------------------------------------------------
        finish_payload = {
            "duration_seconds": 180,
            "overall_notes": "Strong start on database pooling concepts. Ready to practice system design next."
        }
        status, report = self.make_request(
            f"/practice/sessions/{session_id}/finish",
            method="POST",
            data=finish_payload
        )
        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "Completed")
        self.assertGreaterEqual(report["questions_attempted"], 1)
        self.assertIn("criteria_averages", report)

        # -------------------------------------------------------------
        # STEP 8: Verify Dashboard reflects the complete workflow
        # -------------------------------------------------------------
        status, updated_dashboard = self.make_request("/dashboard/summary")
        self.assertEqual(status, 200)
        updated_cards = updated_dashboard["summary_cards"]

        # Job count increased by 1
        self.assertEqual(updated_cards["total_jobs"], initial_job_count + 1)
        # Question count increased by 1
        self.assertEqual(updated_cards["total_questions_saved"], initial_q_count + 1)
        # Sessions completed increased by 1
        self.assertEqual(updated_cards["sessions_completed"], initial_sess_count + 1)

        # Upcoming deadline includes CloudScale Systems
        deadlines = updated_dashboard["upcoming_deadlines"]
        cloudscale_dl = next((d for d in deadlines if d["id"] == job_id), None)
        self.assertIsNotNone(cloudscale_dl)
        self.assertEqual(cloudscale_dl["company_name"], "CloudScale Systems")

        # -------------------------------------------------------------
        # STEP 9: Non-destructive data integrity check
        # -------------------------------------------------------------
        # Deleting the mock session MUST NOT delete the underlying question or job
        status, del_sess_res = self.make_request(f"/practice/sessions/{session_id}", method="DELETE")
        self.assertEqual(status, 200)

        # Verify question still exists
        status, q_check = self.make_request(f"/questions/{question_id}")
        self.assertEqual(status, 200)
        self.assertEqual(q_check["id"], question_id)

        # Verify job still exists
        status, job_check = self.make_request(f"/applications/{job_id}")
        self.assertEqual(status, 200)
        self.assertEqual(job_check["id"], job_id)

        # Deleting analysis history MUST NOT delete the underlying job
        status, del_analysis_res = self.make_request(f"/analyzer/history/{analysis_id}", method="DELETE")
        self.assertEqual(status, 200)

        status, job_check_2 = self.make_request(f"/applications/{job_id}")
        self.assertEqual(status, 200)
        self.assertEqual(job_check_2["id"], job_id)

        # -------------------------------------------------------------
        # CLEANUP: Remove test-created records
        # -------------------------------------------------------------
        self.make_request(f"/questions/{question_id}", method="DELETE")
        self.make_request(f"/applications/{job_id}", method="DELETE")


if __name__ == "__main__":
    unittest.main()
