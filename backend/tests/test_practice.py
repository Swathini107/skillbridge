"""
SkillBridge Test Suite - Mock Interview Practice Studio
Comprehensive verification covering:
1. Previewing a practice session before starting
2. Creating a Technical practice session
3. Creating an HR practice session with preparation guidance
4. Personalization with saved job and Job Description Analyzer data (targeted missing skills)
5. Answering questions with reliable autosave and navigation
6. Skipping a question and verifying attempted vs skipped flags
7. Submitting structured self-assessment ratings and reflections
8. Self-assessment rating validation (must be 1-5)
9. Finishing interview session and generating transparent report
10. Report calculation when ratings are skipped (scores_available=False, no invented scores)
11. Resuming an in-progress session
12. Practice history listing with accurate counts and average scores
13. Non-mutation guarantee (deleting a session preserves original jobs and questions)
14. Including custom manual question in practice session
15. Regression testing Job Saver, Analyzer, and Memory Bank
"""

import os
import unittest
import json
import urllib.request
import urllib.error

BASE_URL = os.getenv("TEST_API_URL", "http://127.0.0.1:8000/api")


class TestMockInterviewPracticeStudio(unittest.TestCase):
    """End-to-end API integration and validation test suite for Practice Studio."""

    def make_request(self, endpoint, method="GET", data=None):
        url = f"{BASE_URL}{endpoint}"
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
        with urllib.request.urlopen(req, data=encoded_data, timeout=10) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)

    @classmethod
    def setUpClass(cls):
        """Seed necessary test questions and job applications for integration tests."""
        # Ensure questions exist in repository
        sample_questions = [
            {
                "question_text": "Explain the difference between SQL JOIN types and when to use an OUTER JOIN.",
                "round_type": "Technical",
                "topic": "SQL",
                "difficulty": "Intermediate",
                "company_name": "Databricks",
                "job_role": "Data Engineer"
            },
            {
                "question_text": "How do you handle asynchronous operations in Python using asyncio?",
                "round_type": "Technical",
                "topic": "Python",
                "difficulty": "Advanced",
                "company_name": "Google",
                "job_role": "Backend Engineer"
            },
            {
                "question_text": "Tell me about a time when you had to prioritize competing project deadlines.",
                "round_type": "HR",
                "topic": "Time Management",
                "difficulty": "Beginner",
                "company_name": "Google",
                "job_role": "Software Engineer"
            },
            {
                "question_text": "Describe a challenging bug you diagnosed and fixed under pressure.",
                "round_type": "Behavioral",
                "topic": "Problem Solving",
                "difficulty": "Intermediate",
                "company_name": "Stripe",
                "job_role": "Full Stack Engineer"
            }
        ]

        for q in sample_questions:
            try:
                url = f"{BASE_URL}/questions"
                req = urllib.request.Request(url, method="POST")
                req.add_header("Content-Type", "application/json")
                urllib.request.urlopen(req, data=json.dumps(q).encode("utf-8"), timeout=5)
            except Exception:
                pass

    def test_01_preview_practice_session(self):
        """1. Preview session configuration and question matching before starting."""
        preview_payload = {
            "session_name": "Technical Interview Test Prep",
            "round_type": "Technical",
            "difficulty": "Mixed",
            "question_count": 5
        }
        status, preview = self.make_request("/practice/preview", method="POST", data=preview_payload)
        self.assertEqual(status, 200)
        self.assertIn("total_available", preview)
        self.assertIn("selected_count", preview)
        self.assertIn("questions", preview)
        self.assertTrue(len(preview["questions"]) > 0)
        self.assertEqual(preview["questions"][0]["round_type"], "Technical")

    def test_02_create_technical_session(self):
        """2. Start a Technical mock interview session."""
        payload = {
            "session_name": "Frontend & Python Mock Interview",
            "round_type": "Technical",
            "target_role": "Full Stack Developer",
            "difficulty": "Mixed",
            "question_count": 5,
            "time_limit_minutes": 15
        }
        status, session = self.make_request("/practice/sessions", method="POST", data=payload)
        self.assertEqual(status, 201)
        self.assertIn("id", session)
        self.assertEqual(session["session_name"], "Frontend & Python Mock Interview")
        self.assertEqual(session["round_type"], "Technical")
        self.assertEqual(session["status"], "In Progress")
        self.assertEqual(session["time_limit_minutes"], 15)
        self.assertTrue(len(session["answers"]) > 0)

        # Verify answer snapshots
        first_q = session["answers"][0]
        self.assertIn("question_text", first_q)
        self.assertEqual(first_q["is_attempted"], False)
        self.assertEqual(first_q["is_skipped"], False)

    def test_03_create_hr_session(self):
        """3. Start an HR mock interview session."""
        payload = {
            "session_name": "Campus HR Screening Round",
            "round_type": "HR",
            "difficulty": "Beginner",
            "question_count": 5,
            "time_limit_minutes": 10
        }
        status, session = self.make_request("/practice/sessions", method="POST", data=payload)
        self.assertEqual(status, 201)
        self.assertEqual(session["round_type"], "HR")
        self.assertTrue(len(session["answers"]) > 0)
        # Verify HR question round
        self.assertEqual(session["answers"][0]["round_type"], "HR")

    def test_04_personalized_session_with_saved_job(self):
        """4. Personalize session using saved job and analyzer missing skills."""
        # Create a saved job
        job_payload = {
            "company_name": "Personalized Cloud Corp",
            "job_title": "Cloud Backend Engineer",
            "application_status": "Interview",
            "skills": "Python, Docker, Kubernetes, AWS"
        }
        _, job = self.make_request("/applications", method="POST", data=job_payload)
        job_id = job["id"]

        # Add a specific question linked to this job
        q_payload = {
            "question_text": "Explain Kubernetes Pod lifecycle and how horizontal pod autoscaling functions.",
            "round_type": "Technical",
            "topic": "Kubernetes",
            "difficulty": "Advanced",
            "company_name": "Personalized Cloud Corp",
            "job_role": "Cloud Backend Engineer",
            "job_id": job_id
        }
        _, linked_q = self.make_request("/questions", method="POST", data=q_payload)

        # Run preview with job_id
        preview_payload = {
            "job_id": job_id,
            "round_type": "Technical",
            "question_count": 5
        }
        _, preview = self.make_request("/practice/preview", method="POST", data=preview_payload)
        self.assertEqual(preview["target_company"], "Personalized Cloud Corp")
        self.assertEqual(preview["target_role"], "Cloud Backend Engineer")

        # The directly linked question should be prioritized at the top
        top_q = preview["questions"][0]
        self.assertEqual(top_q["id"], linked_q["id"])
        self.assertIn("Personalized Cloud Corp", top_q["relevance_reason"])

    def test_05_answer_autosave_and_navigation(self):
        """5. Save student answer and update navigation index and timer duration."""
        # Create a session
        payload = {
            "session_name": "Autosave Navigation Test",
            "round_type": "Technical",
            "question_count": 5
        }
        _, session = self.make_request("/practice/sessions", method="POST", data=payload)
        session_id = session["id"]
        answer_id = session["answers"][0]["id"]

        # Autosave answer
        save_payload = {
            "answer_text": "INNER JOIN returns only matching rows. LEFT OUTER JOIN returns all left rows.",
            "time_spent_seconds": 95
        }
        status, updated_answer = self.make_request(
            f"/practice/sessions/{session_id}/answers/{answer_id}?current_index=1&duration_seconds=120",
            method="PUT",
            data=save_payload
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated_answer["is_attempted"], True)
        self.assertEqual(updated_answer["is_skipped"], False)
        self.assertIn("INNER JOIN", updated_answer["answer_text"])
        self.assertEqual(updated_answer["time_spent_seconds"], 95)

        # Verify session state updated
        _, fetched_session = self.make_request(f"/practice/sessions/{session_id}")
        self.assertEqual(fetched_session["current_question_index"], 1)
        self.assertEqual(fetched_session["duration_seconds"], 120)

    def test_06_skip_question(self):
        """6. Skip question and verify skipped state."""
        payload = {
            "session_name": "Skip Question Test",
            "round_type": "Technical",
            "question_count": 5
        }
        _, session = self.make_request("/practice/sessions", method="POST", data=payload)
        session_id = session["id"]
        answer_id = session["answers"][1]["id"]

        skip_payload = {
            "is_skipped": True,
            "is_attempted": False
        }
        status, answer = self.make_request(
            f"/practice/sessions/{session_id}/answers/{answer_id}",
            method="PUT",
            data=skip_payload
        )
        self.assertEqual(status, 200)
        self.assertEqual(answer["is_skipped"], True)
        self.assertEqual(answer["is_attempted"], False)

    def test_07_structured_self_assessment_ratings(self):
        """7. Submit structured 1-5 ratings on round criteria and reflection notes."""
        payload = {
            "session_name": "Self Assessment Test",
            "round_type": "Technical",
            "question_count": 5
        }
        _, session = self.make_request("/practice/sessions", method="POST", data=payload)
        session_id = session["id"]
        answer_id = session["answers"][0]["id"]

        review_payload = {
            "answer_text": "Explained binary search iterative and recursive approaches with O(log n) time.",
            "self_ratings": {
                "clarity": 4,
                "completeness": 5,
                "confidence": 4,
                "technical_correctness": 5,
                "problem_solving": 4
            },
            "went_well": "Clear explanation of base cases and invariant conditions.",
            "was_difficult": "Took a moment to write the boundary checks for the while loop.",
            "need_to_learn": "Practice bit-shift division vs integer division.",
            "better_approach": "State space complexity upfront before pseudocode."
        }
        status, answer = self.make_request(
            f"/practice/sessions/{session_id}/answers/{answer_id}",
            method="PUT",
            data=review_payload
        )
        self.assertEqual(status, 200)
        self.assertEqual(answer["self_ratings"]["clarity"], 4)
        self.assertEqual(answer["self_ratings"]["technical_correctness"], 5)
        self.assertEqual(answer["went_well"], "Clear explanation of base cases and invariant conditions.")
        self.assertEqual(answer["need_to_learn"], "Practice bit-shift division vs integer division.")

    def test_08_invalid_ratings_validation(self):
        """8. Verify self-assessment scores outside 1-5 return 422 Unprocessable Content."""
        payload = {
            "session_name": "Validation Test",
            "round_type": "Technical",
            "question_count": 5
        }
        _, session = self.make_request("/practice/sessions", method="POST", data=payload)
        session_id = session["id"]
        answer_id = session["answers"][0]["id"]

        invalid_ratings = {
            "self_ratings": {
                "clarity": 6  # Exceeds maximum 5
            }
        }
        url = f"{BASE_URL}/practice/sessions/{session_id}/answers/{answer_id}"
        req = urllib.request.Request(url, method="PUT", data=json.dumps(invalid_ratings).encode("utf-8"))
        req.add_header("Content-Type", "application/json")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 422)

    def test_09_finish_session_and_report_calculation(self):
        """9. Finish session and verify report metrics, criteria averages, and recommendations."""
        payload = {
            "session_name": "Full Interview Run & Report Test",
            "round_type": "Technical",
            "question_count": 5,
            "time_limit_minutes": 15
        }
        _, session = self.make_request("/practice/sessions", method="POST", data=payload)
        session_id = session["id"]

        # Answer 1st question with ratings
        ans1_id = session["answers"][0]["id"]
        self.make_request(
            f"/practice/sessions/{session_id}/answers/{ans1_id}",
            method="PUT",
            data={
                "answer_text": "Detailed explanation of indexing in relational databases.",
                "is_attempted": True,
                "self_ratings": {
                    "clarity": 5,
                    "completeness": 4,
                    "confidence": 4,
                    "technical_correctness": 5,
                    "problem_solving": 4
                }
            }
        )

        # Answer 2nd question with lower rating
        ans2_id = session["answers"][1]["id"]
        self.make_request(
            f"/practice/sessions/{session_id}/answers/{ans2_id}",
            method="PUT",
            data={
                "answer_text": "Basic overview of process vs thread.",
                "is_attempted": True,
                "self_ratings": {
                    "clarity": 3,
                    "completeness": 3,
                    "confidence": 2,
                    "technical_correctness": 3,
                    "problem_solving": 3
                }
            }
        )

        # Skip 3rd question
        ans3_id = session["answers"][2]["id"]
        self.make_request(
            f"/practice/sessions/{session_id}/answers/{ans3_id}",
            method="PUT",
            data={"is_skipped": True}
        )

        # Finish session
        finish_payload = {"duration_seconds": 380}
        status, report = self.make_request(
            f"/practice/sessions/{session_id}/finish",
            method="POST",
            data=finish_payload
        )
        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "Completed")
        self.assertEqual(report["duration_seconds"], 380)
        self.assertEqual(report["questions_attempted"], 2)
        self.assertEqual(report["questions_skipped"], 1)
        self.assertTrue(report["scores_available"])
        self.assertIsNotNone(report["overall_average_score"])
        self.assertIn("clarity", report["criteria_averages"])
        self.assertEqual(report["criteria_averages"]["clarity"], 4.0)  # (5 + 3)/2 = 4.0
        self.assertEqual(report["criteria_averages"]["technical_correctness"], 4.0)  # (5 + 3)/2 = 4.0
        self.assertTrue(len(report["recommendations"]) > 0)

        # Reopen report via GET endpoint
        status, report_get = self.make_request(f"/practice/sessions/{session_id}/report")
        self.assertEqual(status, 200)
        self.assertEqual(report_get["session_id"], session_id)
        self.assertEqual(report_get["questions_attempted"], 2)

    def test_10_report_when_ratings_skipped(self):
        """10. Verify that skipping all ratings produces scores_available=False without invented scores."""
        payload = {
            "session_name": "No Self Ratings Session",
            "round_type": "HR",
            "question_count": 5
        }
        _, session = self.make_request("/practice/sessions", method="POST", data=payload)
        session_id = session["id"]

        # Student writes an answer but leaves self_ratings empty
        ans_id = session["answers"][0]["id"]
        self.make_request(
            f"/practice/sessions/{session_id}/answers/{ans_id}",
            method="PUT",
            data={"answer_text": "Answer text provided without self ratings."}
        )

        _, report = self.make_request(f"/practice/sessions/{session_id}/finish", method="POST")
        self.assertEqual(report["scores_available"], False)
        self.assertIsNone(report["overall_average_score"])
        self.assertEqual(report["criteria_averages"], {})

    def test_11_resume_session(self):
        """11. Resume in-progress session."""
        payload = {
            "session_name": "Resume Session Test",
            "round_type": "Technical",
            "question_count": 5
        }
        _, session = self.make_request("/practice/sessions", method="POST", data=payload)
        session_id = session["id"]

        status, resumed = self.make_request(f"/practice/sessions/{session_id}/resume", method="POST")
        self.assertEqual(status, 200)
        self.assertEqual(resumed["id"], session_id)
        self.assertEqual(resumed["status"], "In Progress")

    def test_12_practice_history_listing(self):
        """12. Revisit previous practice sessions via history endpoint."""
        status, history = self.make_request("/practice/sessions")
        self.assertEqual(status, 200)
        self.assertIsInstance(history, list)
        self.assertTrue(len(history) > 0)

        item = history[0]
        self.assertIn("session_name", item)
        self.assertIn("round_type", item)
        self.assertIn("status", item)
        self.assertIn("total_questions", item)
        self.assertIn("attempted_count", item)

    def test_13_non_mutation_on_deletion(self):
        """13. Deleting a practice session must NOT delete linked jobs or memory bank questions."""
        # Create a job
        _, job = self.make_request("/applications", method="POST", data={
            "company_name": "Immortal Corp",
            "job_title": "Platform Engineer"
        })
        job_id = job["id"]

        # Create a memory bank question
        _, question = self.make_request("/questions", method="POST", data={
            "question_text": "Explain the differences between concurrency and parallelism.",
            "round_type": "Technical",
            "topic": "OS",
            "difficulty": "Intermediate",
            "job_id": job_id
        })
        question_id = question["id"]

        # Create practice session linked to this job
        _, session = self.make_request("/practice/sessions", method="POST", data={
            "session_name": "Temporary Session",
            "job_id": job_id,
            "round_type": "Technical",
            "question_count": 5
        })
        session_id = session["id"]

        # Delete practice session
        del_status, del_resp = self.make_request(f"/practice/sessions/{session_id}", method="DELETE")
        self.assertEqual(del_status, 200)

        # Verify session is deleted
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.make_request(f"/practice/sessions/{session_id}")
        self.assertEqual(ctx.exception.code, 404)

        # Verify job STILL EXISTS (non-mutation guarantee!)
        job_status, fetched_job = self.make_request(f"/applications/{job_id}")
        self.assertEqual(job_status, 200)
        self.assertEqual(fetched_job["company_name"], "Immortal Corp")

        # Verify question STILL EXISTS (non-mutation guarantee!)
        q_status, fetched_q = self.make_request(f"/questions/{question_id}")
        self.assertEqual(q_status, 200)
        self.assertIn("concurrency", fetched_q["question_text"])

    def test_14_custom_question_inclusion(self):
        """14. Include a custom manual question in the practice session."""
        payload = {
            "session_name": "Custom Question Session",
            "round_type": "Technical",
            "question_count": 5,
            "custom_question": {
                "question_text": "Write a function to detect a cycle in a singly linked list using Floyd's Tortoise and Hare.",
                "round_type": "Technical",
                "topic": "Data Structures",
                "difficulty": "Intermediate",
                "expected_answer": "Use two pointers, slow (1 step) and fast (2 steps). If they meet, a cycle exists."
            }
        }
        status, session = self.make_request("/practice/sessions", method="POST", data=payload)
        self.assertEqual(status, 201)
        # Custom question is prepended as first answer
        first_ans = session["answers"][0]
        self.assertIn("Tortoise and Hare", first_ans["question_text"])
        self.assertEqual(first_ans["question_id"], None)  # Source is custom manual question

    def test_15_regression_existing_modules(self):
        """15. Regression test: Saved jobs, analyzer, and questions remain fully functional."""
        # Job Applications
        status, app_stats = self.make_request("/applications/stats")
        self.assertEqual(status, 200)
        self.assertIn("total_jobs", app_stats)

        # Job Analyzer
        status, analysis = self.make_request("/analyzer/analyze", method="POST", data={
            "job_description": "We need a React and Node.js developer with PostgreSQL expertise.",
            "candidate_profile": "Built applications using React and PostgreSQL."
        })
        self.assertEqual(status, 200)
        self.assertIn("match_score", analysis)
        self.assertIn("missing_skills", analysis)

        # Interview Questions
        status, q_stats = self.make_request("/questions/stats")
        self.assertEqual(status, 200)
        self.assertIn("total", q_stats)


if __name__ == "__main__":
    unittest.main()
