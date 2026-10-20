"""
SkillBridge Test Suite - Interview Memory Bank
Comprehensive verification covering:
1. Technical and HR question creation (201 Created)
2. Question creation with all optional fields
3. Editing a question and verifying persistent updates
4. Deleting a question and verifying 404 on subsequent retrieval
5. Searching questions across text, company, and topic
6. Filtering by round type, difficulty, and review status
7. Patching review status and verifying statistics calculations
8. Linking question to a saved job application
9. Job non-mutation guarantee (editing/deleting question preserves job status and data)
10. Input validation errors (empty text, short text, invalid choices return HTTP 422)
11. Regression tests for Application Tracker and Job Analyzer
"""

import os
import unittest
import json
import urllib.request
import urllib.error

BASE_URL = os.getenv("TEST_API_URL", "http://127.0.0.1:8000/api")


class TestInterviewMemoryBank(unittest.TestCase):
    """End-to-end API integration and validation test suite for Interview Memory Bank"""

    def make_request(self, endpoint, method="GET", data=None):
        url = f"{BASE_URL}{endpoint}"
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
        with urllib.request.urlopen(req, data=encoded_data, timeout=10) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)

    def test_01_create_technical_and_hr_questions(self):
        """1. Create a Technical question and an HR question"""
        tech_payload = {
            "question_text": "Explain how React reconciliation and the Virtual DOM diffing algorithm work.",
            "round_type": "Technical",
            "topic": "React",
            "difficulty": "Intermediate"
        }
        status, tech_q = self.make_request("/questions", method="POST", data=tech_payload)
        self.assertEqual(status, 201)
        self.assertIn("id", tech_q)
        self.assertEqual(tech_q["round_type"], "Technical")
        self.assertEqual(tech_q["topic"], "React")
        self.assertEqual(tech_q["review_status"], "New")

        hr_payload = {
            "question_text": "Tell me about a time you had a disagreement with a team member and how you resolved it.",
            "round_type": "HR",
            "topic": "Conflict Resolution",
            "difficulty": "Beginner"
        }
        status, hr_q = self.make_request("/questions", method="POST", data=hr_payload)
        self.assertEqual(status, 201)
        self.assertIn("id", hr_q)
        self.assertEqual(hr_q["round_type"], "HR")
        self.assertEqual(hr_q["topic"], "Conflict Resolution")

        # Clean up
        self.make_request(f"/questions/{tech_q['id']}", method="DELETE")
        self.make_request(f"/questions/{hr_q['id']}", method="DELETE")

    def test_02_create_question_with_all_optional_fields(self):
        """2. Create a question with all optional fields filled"""
        full_payload = {
            "question_text": "Design a rate limiter for a public API gateway that handles 10,000 requests per second.",
            "round_type": "System Design",
            "topic": "System Design",
            "difficulty": "Advanced",
            "company_name": "Cloudflare",
            "job_role": "Backend Infrastructure Intern",
            "interview_date": "2026-10-15",
            "source": "Personal interview",
            "original_answer": "I suggested using Token Bucket algorithm with Redis for distributed counters.",
            "expected_answer": "Token Bucket or Leaky Bucket with sliding window; discuss Redis clustering and race conditions.",
            "improvement_notes": "Next time calculate memory footprint for 10k RPS explicitly before jumping to Redis.",
            "tags": "Rate Limiting, Redis, Scalability, System Architecture",
            "review_status": "Learning"
        }
        status, q = self.make_request("/questions", method="POST", data=full_payload)
        self.assertEqual(status, 201)
        self.assertEqual(q["company_name"], "Cloudflare")
        self.assertEqual(q["job_role"], "Backend Infrastructure Intern")
        self.assertEqual(q["round_type"], "System Design")
        self.assertEqual(q["difficulty"], "Advanced")
        self.assertEqual(q["source"], "Personal interview")
        self.assertEqual(q["review_status"], "Learning")
        self.assertIn("Token Bucket", q["original_answer"])
        self.assertIn("Rate Limiting", q["tags"])

        # Clean up
        self.make_request(f"/questions/{q['id']}", method="DELETE")

    def test_03_edit_question_persistence(self):
        """3. Edit the question and verify that the changes persist"""
        # Create initial
        status, q = self.make_request("/questions", method="POST", data={
            "question_text": "What is the difference between SQL and NoSQL databases?",
            "round_type": "Technical",
            "topic": "Databases",
            "difficulty": "Beginner"
        })
        self.assertEqual(status, 201)
        q_id = q["id"]

        # Edit
        update_payload = {
            "difficulty": "Intermediate",
            "topic": "Relational Databases",
            "expected_answer": "ACID compliance, schema rigidity, horizontal vs vertical scaling comparison.",
            "review_status": "Confident"
        }
        status, updated = self.make_request(f"/questions/{q_id}", method="PUT", data=update_payload)
        self.assertEqual(status, 200)
        self.assertEqual(updated["difficulty"], "Intermediate")
        self.assertEqual(updated["topic"], "Relational Databases")
        self.assertEqual(updated["review_status"], "Confident")

        # Fetch independently to verify persistence
        status, fetched = self.make_request(f"/questions/{q_id}", method="GET")
        self.assertEqual(status, 200)
        self.assertEqual(fetched["difficulty"], "Intermediate")
        self.assertEqual(fetched["topic"], "Relational Databases")
        self.assertEqual(fetched["review_status"], "Confident")
        self.assertIn("ACID compliance", fetched["expected_answer"])

        # Clean up
        self.make_request(f"/questions/{q_id}", method="DELETE")

    def test_04_delete_question_and_verify_404(self):
        """4. Delete a question and verify that it is no longer retrievable"""
        status, q = self.make_request("/questions", method="POST", data={
            "question_text": "Explain Python GIL and why it matters for multi-threading."
        })
        self.assertEqual(status, 201)
        q_id = q["id"]

        # Delete
        status, del_res = self.make_request(f"/questions/{q_id}", method="DELETE")
        self.assertEqual(status, 200)
        self.assertTrue(del_res.get("success"))

        # Verify 404
        url = f"{BASE_URL}/questions/{q_id}"
        req = urllib.request.Request(url, method="GET")
        try:
            urllib.request.urlopen(req, timeout=5)
            self.fail("Expected HTTP 404 Not Found")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)

    def test_05_search_by_text_company_and_topic(self):
        """5. Search by question text, company, and topic"""
        # Create sample questions
        q1_payload = {
            "question_text": "Write a function to invert a binary tree in place.",
            "company_name": "Meta",
            "topic": "Binary Trees",
            "tags": "Trees, Recursion, LeetCode"
        }
        q2_payload = {
            "question_text": "Describe your greatest strength and your greatest weakness.",
            "company_name": "Amazon",
            "topic": "Self Assessment",
            "tags": "HR, Behavioral, Soft Skills"
        }
        _, q1 = self.make_request("/questions", method="POST", data=q1_payload)
        _, q2 = self.make_request("/questions", method="POST", data=q2_payload)

        # Search by text
        status, results = self.make_request("/questions?search=binary+tree", method="GET")
        self.assertEqual(status, 200)
        ids = [item["id"] for item in results]
        self.assertIn(q1["id"], ids)
        self.assertNotIn(q2["id"], ids)

        # Search by company
        status, results = self.make_request("/questions?search=Amazon", method="GET")
        self.assertEqual(status, 200)
        ids = [item["id"] for item in results]
        self.assertIn(q2["id"], ids)
        self.assertNotIn(q1["id"], ids)

        # Search by topic
        status, results = self.make_request("/questions?search=Self+Assessment", method="GET")
        self.assertEqual(status, 200)
        ids = [item["id"] for item in results]
        self.assertIn(q2["id"], ids)

        # Clean up
        self.make_request(f"/questions/{q1['id']}", method="DELETE")
        self.make_request(f"/questions/{q2['id']}", method="DELETE")

    def test_06_filter_by_round_difficulty_and_status(self):
        """6. Filter by round type, difficulty, and review status"""
        q_payload = {
            "question_text": "What is the time complexity of QuickSort in the worst case?",
            "round_type": "Technical",
            "difficulty": "Beginner",
            "review_status": "New"
        }
        _, q = self.make_request("/questions", method="POST", data=q_payload)

        # Match filter
        status, matches = self.make_request("/questions?round_type=Technical&difficulty=Beginner&review_status=New", method="GET")
        self.assertEqual(status, 200)
        self.assertTrue(any(item["id"] == q["id"] for item in matches))

        # Mismatch filter
        status, mismatches = self.make_request("/questions?round_type=HR", method="GET")
        self.assertEqual(status, 200)
        self.assertFalse(any(item["id"] == q["id"] for item in mismatches))

        # Clean up
        self.make_request(f"/questions/{q['id']}", method="DELETE")

    def test_07_status_patch_and_stats_update(self):
        """7. Change review status via PATCH and verify that statistics update"""
        # Create question with status "New"
        _, q = self.make_request("/questions", method="POST", data={
            "question_text": "How do index scans differ from full table scans in PostgreSQL?",
            "round_type": "Technical",
            "review_status": "New"
        })

        # Fetch baseline stats
        status, stats_before = self.make_request("/questions/stats", method="GET")
        self.assertEqual(status, 200)
        confident_before = stats_before["confident"]
        needs_review_before = stats_before["needs_review"]

        # PATCH status to Confident
        status, patch_res = self.make_request(f"/questions/{q['id']}/status", method="PATCH", data={
            "review_status": "Confident"
        })
        self.assertEqual(status, 200)
        self.assertEqual(patch_res["review_status"], "Confident")

        # Fetch stats after
        status, stats_after = self.make_request("/questions/stats", method="GET")
        self.assertEqual(status, 200)
        self.assertEqual(stats_after["confident"], confident_before + 1)
        self.assertEqual(stats_after["needs_review"], needs_review_before - 1)

        # Clean up
        self.make_request(f"/questions/{q['id']}", method="DELETE")

    def test_08_link_question_to_saved_job(self):
        """8. Associate a question with an existing saved job"""
        # 1. Fetch available jobs
        status, jobs = self.make_request("/applications", method="GET")
        self.assertEqual(status, 200)
        self.assertTrue(len(jobs) > 0, "Requires at least one tracked job application")
        target_job = jobs[0]
        job_id = target_job["id"]

        # 2. Create question referencing job_id
        q_payload = {
            "question_text": "Describe the architecture of the distributed cache service you built.",
            "job_id": job_id,
            "round_type": "Technical"
        }
        status, q = self.make_request("/questions", method="POST", data=q_payload)
        self.assertEqual(status, 201)
        self.assertEqual(q["job_id"], job_id)
        # Should auto-fill company and role if not specified
        self.assertEqual(q["company_name"], target_job["company_name"])
        self.assertEqual(q["job_role"], target_job["job_title"])

        # Clean up
        self.make_request(f"/questions/{q['id']}", method="DELETE")

    def test_09_job_non_mutation_on_question_edit_or_delete(self):
        """9. Verify that editing or deleting a question does not modify the associated job"""
        # 1. Get existing job
        status, jobs = self.make_request("/applications", method="GET")
        target_job = jobs[0]
        job_id = target_job["id"]
        orig_status = target_job["application_status"]
        orig_desc = target_job.get("job_description")
        orig_notes = target_job.get("notes")

        # 2. Create linked question
        status, q = self.make_request("/questions", method="POST", data={
            "question_text": "What is the two pointer technique and when should it be used?",
            "job_id": job_id,
            "round_type": "Technical"
        })
        self.assertEqual(status, 201)
        q_id = q["id"]

        # 3. Edit question
        self.make_request(f"/questions/{q_id}", method="PUT", data={
            "expected_answer": "Used for sorted arrays, palindrome checking, sliding windows.",
            "difficulty": "Intermediate"
        })

        # 4. Delete question
        self.make_request(f"/questions/{q_id}", method="DELETE")

        # 5. Check job is completely unchanged
        status, job_after = self.make_request(f"/applications/{job_id}", method="GET")
        self.assertEqual(status, 200)
        self.assertEqual(job_after["application_status"], orig_status)
        self.assertEqual(job_after.get("job_description"), orig_desc)
        self.assertEqual(job_after.get("notes"), orig_notes)

    def test_10_validation_errors(self):
        """10. Validate missing required fields and invalid values"""
        # Missing question_text
        try:
            self.make_request("/questions", method="POST", data={
                "question_text": "",
                "round_type": "Technical"
            })
            self.fail("Expected HTTP 422 for blank question_text")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 422)

        # Question text too short
        try:
            self.make_request("/questions", method="POST", data={
                "question_text": "Why?",
                "round_type": "Technical"
            })
            self.fail("Expected HTTP 422 for question_text shorter than 5 chars")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 422)

        # Invalid round_type
        try:
            self.make_request("/questions", method="POST", data={
                "question_text": "Valid question text here",
                "round_type": "InvalidRoundName"
            })
            self.fail("Expected HTTP 422 for invalid round_type")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 422)

        # Invalid difficulty
        try:
            self.make_request("/questions", method="POST", data={
                "question_text": "Valid question text here",
                "difficulty": "SuperHard"
            })
            self.fail("Expected HTTP 422 for invalid difficulty")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 422)

    def test_11_day_2_applications_and_day_3_analyzer_regression(self):
        """11. Verify that application tracker and job analyzer continue to function"""
        # Job Application Stats
        status, app_stats = self.make_request("/applications/stats", method="GET")
        self.assertEqual(status, 200)
        self.assertIn("total_jobs", app_stats)

        # Job Analyzer
        analyzer_payload = {
            "job_description": "We are seeking a React and Python developer with Git skills.",
            "resume_or_profile_text": "Proficient in React and Git.",
            "save_analysis": False
        }
        status, analysis = self.make_request("/analyzer/analyze", method="POST", data=analyzer_payload)
        self.assertEqual(status, 200)
        self.assertIn("match_score", analysis)
        self.assertGreater(analysis["match_score"], 0)


if __name__ == "__main__":
    unittest.main()
