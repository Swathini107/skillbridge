"""
SkillBridge Test Suite - Job Description Analyzer
Covers:
1. Unit tests for analyze_job_and_profile (6 representative scenarios, aliases, boundaries, scoring)
2. API integration tests (Analyze endpoint, History listing, Detail, Delete)
3. Validation tests (short description, empty fields)
4. Saved job non-mutation (analyzing a saved job preserves description and status)
5. Application Tracker regression (jobs listing, add, update, delete)
"""

import os
import unittest
import json
import urllib.request
import urllib.error
from app.services.skill_extractor import analyze_job_and_profile

BASE_URL = os.getenv("TEST_API_URL", "http://127.0.0.1:8000/api")

class TestSkillExtractorUnit(unittest.TestCase):
    """Direct unit testing of the extraction, classification, and scoring service"""

    def test_case_1_frontend_internship(self):
        """1. Frontend development internship"""
        jd = """
        Frontend Developer Intern
        Requirements:
        Must have strong skills in HTML, CSS, and JavaScript.
        Experience with React is required.
        Knowledge of Git version control.
        """
        profile = "Proficient in HTML, CSS, and JavaScript. Have built small projects with React."
        res = analyze_job_and_profile(jd, profile)

        req_names = [s["skill"] for s in res["required_skills"]]
        self.assertIn("HTML", req_names)
        self.assertIn("CSS", req_names)
        self.assertIn("JavaScript", req_names)
        self.assertIn("React", req_names)
        self.assertIn("Git", req_names)

        match_req = [s["skill"] for s in res["matching_required"]]
        self.assertIn("HTML", match_req)
        self.assertIn("CSS", match_req)
        self.assertIn("JavaScript", match_req)
        self.assertIn("React", match_req)

        missing_req = [s["skill"] for s in res["missing_required"]]
        self.assertIn("Git", missing_req)

        self.assertIsNotNone(res["match_score"])
        self.assertGreater(res["match_score"], 70)

    def test_case_2_python_data_science_internship(self):
        """2. Python and data science internship"""
        jd = """
        Data Science Intern
        Required Qualifications:
        - Python programming
        - SQL database querying
        - Pandas and NumPy for data manipulation
        Preferred Qualifications:
        - Machine learning fundamentals with scikit-learn
        - Experience with Exploratory Data Analysis (EDA)
        """
        profile = "Strong Python and SQL knowledge. Experience using Pandas."
        res = analyze_job_and_profile(jd, profile)

        req_names = [s["skill"] for s in res["required_skills"]]
        pref_names = [s["skill"] for s in res["preferred_skills"]]

        self.assertIn("Python", req_names)
        self.assertIn("SQL", req_names)
        self.assertIn("Pandas", req_names)
        self.assertIn("NumPy", req_names)
        self.assertIn("Machine Learning", pref_names)
        self.assertIn("Scikit-learn", pref_names)
        self.assertIn("Exploratory Data Analysis", pref_names)

        match_req = [s["skill"] for s in res["matching_required"]]
        self.assertIn("Python", match_req)
        self.assertIn("SQL", match_req)
        self.assertIn("Pandas", match_req)
        self.assertNotIn("NumPy", match_req)

        missing_pref = [s["skill"] for s in res["missing_preferred"]]
        self.assertIn("Machine Learning", missing_pref)
        self.assertIn("Scikit-learn", missing_pref)
        self.assertIn("Exploratory Data Analysis", missing_pref)

        # Formula: 3/4 req (75%) * 70 = 52.5, 0/3 pref (0%) * 30 = 0 -> Total = 52.5%
        self.assertEqual(res["match_score"], 52.5)

    def test_case_3_fullstack_internship(self):
        """3. Full-stack development internship"""
        jd = """
        Full Stack Intern
        Must have:
        - JavaScript or TypeScript
        - React and Node.js
        - REST APIs and PostgreSQL
        - Data Structures and Algorithms
        """
        profile = "Skilled in JavaScript, React, Node.js, and REST APIs. Familiar with Data Structures."
        res = analyze_job_and_profile(jd, profile)

        req_names = [s["skill"] for s in res["required_skills"]]
        self.assertIn("JavaScript", req_names)
        self.assertIn("TypeScript", req_names)
        self.assertIn("React", req_names)
        self.assertIn("Node.js", req_names)
        self.assertIn("REST APIs", req_names)
        self.assertIn("PostgreSQL", req_names)
        self.assertIn("Data Structures & Algorithms", req_names)

        match_req = [s["skill"] for s in res["matching_required"]]
        self.assertIn("JavaScript", match_req)
        self.assertIn("React", match_req)
        self.assertIn("Node.js", match_req)
        self.assertIn("REST APIs", match_req)

        missing_req = [s["skill"] for s in res["missing_required"]]
        self.assertIn("PostgreSQL", missing_req)

    def test_case_4_preferred_and_required_sections(self):
        """4. A description with both preferred and required skills"""
        jd = """
        Software Engineer
        Must-have skills:
        - FastAPI
        - SQLite
        Nice-to-have skills:
        - Docker
        """
        profile = "FastAPI developer with Docker knowledge."
        res = analyze_job_and_profile(jd, profile)

        req_names = [s["skill"] for s in res["required_skills"]]
        pref_names = [s["skill"] for s in res["preferred_skills"]]

        self.assertIn("FastAPI", req_names)
        self.assertIn("SQLite", req_names)
        self.assertIn("Docker", pref_names)

        # Formula check:
        # req_coverage = 1/2 = 50%, pref_coverage = 1/1 = 100%
        # total = (0.7 * 0.5 + 0.3 * 1.0) * 100 = 35 + 30 = 65%
        self.assertEqual(res["match_score"], 65.0)
        self.assertIn("0.70", res["score_breakdown"]["formula"])

    def test_case_5_no_recognizable_technical_skills(self):
        """5. A description with no recognizable technical skills"""
        jd = """
        Office Operations Associate
        Looking for a friendly individual who has great punctuality, communication skills,
        and thrives in a fast-paced energetic office environment.
        """
        profile = "Motivated college student looking for an exciting position."
        res = analyze_job_and_profile(jd, profile)

        # Should handle gracefully with None score and clear message
        self.assertIsNone(res["match_score"])
        self.assertIn("No recognizable technical skills", res["score_breakdown"]["message"])
        self.assertEqual(len(res["required_skills"]), 0)
        self.assertEqual(len(res["preferred_skills"]), 0)

    def test_case_6_alias_detection(self):
        """6. A description containing aliases such as JS, ReactJS, and ML"""
        jd = """
        AI & Web Developer
        Qualifications:
        - Proficient in JS and ReactJS
        - Strong background in ML and NLP
        - Familiar with EDA and Git version control
        """
        profile = "Experienced in JavaScript, React, and Machine Learning."
        res = analyze_job_and_profile(jd, profile)

        all_detected = [s["skill"] for s in res["required_skills"] + res["preferred_skills"] + res["unclassified_skills"]]
        self.assertIn("JavaScript", all_detected)
        self.assertIn("React", all_detected)
        self.assertIn("Machine Learning", all_detected)
        self.assertIn("Natural Language Processing", all_detected)
        self.assertIn("Exploratory Data Analysis", all_detected)
        self.assertIn("Git", all_detected)

        # Check matched aliases have evidence
        all_skills = res["required_skills"] + res["preferred_skills"] + res["unclassified_skills"]
        js_skill = next(s for s in all_skills if s["skill"] == "JavaScript")
        self.assertEqual(js_skill["matched_alias"].lower(), "js")

        react_skill = next(s for s in all_skills if s["skill"] == "React")
        self.assertEqual(react_skill["matched_alias"].lower(), "reactjs")

        ml_skill = next(s for s in all_skills if s["skill"] == "Machine Learning")
        self.assertEqual(ml_skill["matched_alias"].lower(), "ml")

    def test_prioritized_recommendations(self):
        """Verify recommendations give high priority to required gaps and practical action"""
        jd = """
        Required Qualifications:
        - React
        - Docker
        """
        profile = "Junior developer with basic skills"
        res = analyze_job_and_profile(jd, profile)

        recs = res["recommendations"]
        self.assertTrue(len(recs) >= 2)
        react_rec = next((r for r in recs if r["skill"] == "React"), None)
        self.assertIsNotNone(react_rec)
        self.assertEqual(react_rec["priority"], "High")
        self.assertIn("React", react_rec["suggested_action"])


class TestAnalyzerAPIIntegration(unittest.TestCase):
    """End-to-end API integration tests against the live FastAPI backend"""

    def make_request(self, endpoint, method="GET", data=None):
        url = f"{BASE_URL}{endpoint}"
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
        with urllib.request.urlopen(req, data=encoded_data, timeout=10) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)

    def test_api_analyze_and_history_lifecycle(self):
        """Test POST /analyzer/analyze, GET /history, GET /history/{id}, and DELETE /history/{id}"""
        payload = {
            "company_name": "Acme Labs",
            "job_title": "Full Stack Intern",
            "job_description": "We are seeking an intern with strong React, Node.js, and SQL skills.",
            "resume_or_profile_text": "I know React and SQL very well.",
            "save_analysis": True
        }
        status, data = self.make_request("/analyzer/analyze", method="POST", data=payload)
        self.assertEqual(status, 200)
        self.assertIn("id", data)
        self.assertIsNotNone(data["id"])
        analysis_id = data["id"]
        self.assertEqual(data["company_name"], "Acme Labs")
        self.assertEqual(data["job_title"], "Full Stack Intern")

        # Verify listed in history
        status, hist = self.make_request("/analyzer/history", method="GET")
        self.assertEqual(status, 200)
        hist_ids = [item["id"] for item in hist]
        self.assertIn(analysis_id, hist_ids)

        # Verify retrieve single analysis
        status, item = self.make_request(f"/analyzer/history/{analysis_id}", method="GET")
        self.assertEqual(status, 200)
        self.assertEqual(item["id"], analysis_id)
        self.assertEqual(item["company_name"], "Acme Labs")

        # Verify delete analysis
        status, del_resp = self.make_request(f"/analyzer/history/{analysis_id}", method="DELETE")
        self.assertEqual(status, 200)
        self.assertTrue(del_resp.get("success"))

        # Verify no longer in history
        status, hist_after = self.make_request("/analyzer/history", method="GET")
        self.assertEqual(status, 200)
        hist_after_ids = [item["id"] for item in hist_after]
        self.assertNotIn(analysis_id, hist_after_ids)

    def test_api_validation_short_description(self):
        """Verify API returns 422 error for empty or too short job descriptions"""
        payload = {
            "job_description": "Too short",
            "resume_or_profile_text": "Python dev"
        }
        url = f"{BASE_URL}/analyzer/analyze"
        req = urllib.request.Request(url, method="POST")
        req.add_header("Content-Type", "application/json")
        try:
            urllib.request.urlopen(req, data=json.dumps(payload).encode("utf-8"), timeout=5)
            self.fail("Expected HTTP 422 Unprocessable Entity")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 422)

    def test_saved_job_analysis_does_not_mutate_job(self):
        """Verify analyzing a saved job associates the analysis without altering job status or description"""
        # 1. Fetch current jobs
        status, jobs = self.make_request("/applications", method="GET")
        self.assertEqual(status, 200)
        self.assertTrue(len(jobs) > 0, "Expected at least one job in tracker")
        target_job = jobs[0]
        job_id = target_job["id"]
        original_status = target_job["application_status"]
        original_desc = target_job.get("job_description")

        # 2. Run analysis referencing job_id
        payload = {
            "job_id": job_id,
            "company_name": target_job["company_name"],
            "job_title": target_job["job_title"],
            "job_description": original_desc or "Looking for Python, FastAPI, and SQL developer.",
            "resume_or_profile_text": "Proficient in Python and FastAPI.",
            "save_analysis": True
        }
        status, analysis = self.make_request("/analyzer/analyze", method="POST", data=payload)
        self.assertEqual(status, 200)
        self.assertEqual(analysis["job_id"], job_id)

        # 3. Fetch the job again and verify status and description are strictly unchanged
        status, fetched_job = self.make_request(f"/applications/{job_id}", method="GET")
        self.assertEqual(status, 200)
        self.assertEqual(fetched_job["application_status"], original_status)
        self.assertEqual(fetched_job.get("job_description"), original_desc)

        # Cleanup analysis
        if analysis.get("id"):
            self.make_request(f"/analyzer/history/{analysis['id']}", method="DELETE")

    def test_day_2_applications_crud_regression(self):
        """Verify Application Tracker functions continue to work flawlessly"""
        # Test Create
        new_app = {
            "company_name": "TestCorp Regression",
            "job_title": "Backend Intern",
            "application_status": "Saved",
            "job_description": "Building microservices with Python and FastAPI.",
            "skills": "Python, FastAPI"
        }
        status, created = self.make_request("/applications", method="POST", data=new_app)
        self.assertEqual(status, 201)
        created_id = created["id"]
        self.assertEqual(created["company_name"], "TestCorp Regression")

        # Test Update Status
        status, updated = self.make_request(
            f"/applications/{created_id}",
            method="PUT",
            data={"application_status": "Applied"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["application_status"], "Applied")

        # Test Filter / Search
        status, search_res = self.make_request("/applications?search=TestCorp", method="GET")
        self.assertEqual(status, 200)
        self.assertTrue(any(j["id"] == created_id for j in search_res))

        # Test Delete
        status, del_res = self.make_request(f"/applications/{created_id}", method="DELETE")
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
