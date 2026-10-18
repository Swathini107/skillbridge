"""
SkillBridge ATS-Friendly Resume Builder Test Suite
Verifies:
1. Resume creation, retrieval, and updating
2. Multi-draft independence and isolation (updating draft A doesn't mutate draft B)
3. Duplication creates isolated new records with copied content
4. Safe, non-destructive deletion (deleting a resume never deletes linked jobs or analyses)
5. Transparent, rule-based ATS quality review (0-100 score, critical issues, strong verbs, vague phrases)
6. Target job keyword tailoring and truthful alignment recommendations
7. DOCX export generating valid, compliant OpenXML documents with resume text
8. Sample resume endpoint providing verified student templates
9. Proper 404 handling for non-existent records
"""

import os
import unittest
import json
import urllib.request
import urllib.error
import zipfile
import io

BASE_URL = os.getenv("TEST_API_URL", "http://127.0.0.1:8000/api")


class TestResumeBuilder(unittest.TestCase):
    """API integration test suite for the ATS-Friendly Resume Builder."""

    def make_request(self, endpoint, method="GET", data=None):
        url = f"{BASE_URL}{endpoint}"
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
        try:
            with urllib.request.urlopen(req, data=encoded_data, timeout=10) as response:
                body = response.read()
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return response.status, json.loads(body.decode("utf-8")), response.headers
                return response.status, body, response.headers
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                parsed = json.loads(err_body)
            except Exception:
                parsed = {"detail": err_body}
            return e.code, parsed, e.headers

    def test_01_create_and_retrieve_resume(self):
        """Test creating a resume draft and retrieving it by ID."""
        payload = {
            "title": "Software Engineering Placement Resume",
            "target_role": "Full-Stack Developer",
            "contact_info": {
                "full_name": "Jordan Smith",
                "email": "jordan.smith@university.edu",
                "phone": "+1 555-0192",
                "location": "Boston, MA",
                "linkedin_url": "https://linkedin.com/in/jordansmith-dev",
                "github_url": "https://github.com/jordansmith",
                "portfolio_url": "https://jordansmith.dev"
            },
            "summary": "Motivated Computer Science graduate proficient in Python, React, and REST API development.",
            "skills": [
                {"category": "Programming Languages", "items": ["Python", "JavaScript", "TypeScript"]},
                {"category": "Web Frameworks", "items": ["React", "FastAPI", "Node.js"]}
            ],
            "education": [
                {
                    "institution": "Boston University",
                    "degree": "B.S. Computer Science",
                    "field_of_study": "Computer Science",
                    "start_date": "2021",
                    "graduation_date": "2025",
                    "gpa": "3.85 / 4.0",
                    "coursework": "Data Structures, Database Management, Algorithms"
                }
            ],
            "projects": [
                {
                    "title": "Cloud Job Tracker",
                    "description": "Full-stack job application tracker with status tracking",
                    "technologies": ["React", "FastAPI", "SQLite"],
                    "bullets": [
                        "Engineered responsive user interface using React and custom CSS.",
                        "Implemented secure REST endpoints in FastAPI, improving response speeds by 25%."
                    ]
                }
            ],
            "experience": []
        }

        status, created, _ = self.make_request("/resumes", method="POST", data=payload)
        self.assertEqual(status, 201)
        self.assertIn("id", created)
        resume_id = created["id"]
        self.assertEqual(created["title"], payload["title"])
        self.assertEqual(created["contact_info"]["full_name"], "Jordan Smith")

        # Retrieve by ID
        status_get, fetched, _ = self.make_request(f"/resumes/{resume_id}")
        self.assertEqual(status_get, 200)
        self.assertEqual(fetched["id"], resume_id)
        self.assertEqual(fetched["summary"], payload["summary"])
        self.assertEqual(len(fetched["skills"]), 2)
        self.assertEqual(len(fetched["projects"]), 1)

    def test_02_update_resume(self):
        """Test modifying an existing resume draft and confirming persistence."""
        # Create draft
        status, created, _ = self.make_request("/resumes", method="POST", data={"title": "Draft Before Update"})
        self.assertEqual(status, 201)
        resume_id = created["id"]

        # Update
        update_payload = {
            "title": "Draft After Update",
            "summary": "Updated summary describing backend specialization in Python and PostgreSQL.",
            "skills": [
                {"category": "Backend", "items": ["Python", "FastAPI", "PostgreSQL", "Docker"]}
            ]
        }
        status_put, updated, _ = self.make_request(f"/resumes/{resume_id}", method="PUT", data=update_payload)
        self.assertEqual(status_put, 200)
        self.assertEqual(updated["title"], "Draft After Update")
        self.assertEqual(updated["summary"], update_payload["summary"])
        self.assertEqual(len(updated["skills"]), 1)
        self.assertEqual(updated["skills"][0]["category"], "Backend")

    def test_03_multiple_drafts_isolation(self):
        """Verify that updating one resume draft does not alter or corrupt another draft."""
        status_a, draft_a, _ = self.make_request(
            "/resumes", method="POST", data={"title": "Frontend Track Resume", "target_role": "Frontend Developer"}
        )
        self.assertEqual(status_a, 201)

        status_b, draft_b, _ = self.make_request(
            "/resumes", method="POST", data={"title": "Data Science Track Resume", "target_role": "Data Science Intern"}
        )
        self.assertEqual(status_b, 201)

        # Mutate draft A
        self.make_request(
            f"/resumes/{draft_a['id']}",
            method="PUT",
            data={"title": "Frontend Track Resume (MODIFIED)", "summary": "Frontend Specialist with React and Redux"}
        )

        # Verify draft B remains completely unchanged
        _, fetched_b, _ = self.make_request(f"/resumes/{draft_b['id']}")
        self.assertEqual(fetched_b["title"], "Data Science Track Resume")
        self.assertEqual(fetched_b["target_role"], "Data Science Intern")
        self.assertNotEqual(fetched_b["summary"], "Frontend Specialist with React and Redux")

    def test_04_duplicate_resume(self):
        """Verify resume duplication produces an independent copy with a new ID."""
        orig_payload = {
            "title": "Master Base Resume",
            "target_role": "Software Engineer",
            "contact_info": {"full_name": "Taylor Swift", "email": "taylor@example.com"}
        }
        status, orig, _ = self.make_request("/resumes", method="POST", data=orig_payload)
        self.assertEqual(status, 201)
        orig_id = orig["id"]

        # Duplicate
        status_dup, dup, _ = self.make_request(f"/resumes/{orig_id}/duplicate", method="POST")
        self.assertEqual(status_dup, 201)
        self.assertNotEqual(dup["id"], orig_id)
        self.assertIn("Master Base Resume (Copy)", dup["title"])
        self.assertEqual(dup["contact_info"]["full_name"], "Taylor Swift")

        # Mutating copy doesn't alter original
        self.make_request(f"/resumes/{dup['id']}", method="PUT", data={"title": "Customized Copy"})
        _, check_orig, _ = self.make_request(f"/resumes/{orig_id}")
        self.assertEqual(check_orig["title"], "Master Base Resume")

    def test_05_delete_resume_non_destructive(self):
        """Deleting a resume draft must never delete linked jobs or job analyses."""
        # Create a job first
        job_payload = {
            "company_name": "PreservedCompany",
            "job_title": "Platform Engineer",
            "application_status": "Applied"
        }
        status_job, job, _ = self.make_request("/applications", method="POST", data=job_payload)
        self.assertEqual(status_job, 201)
        job_id = job["id"]

        # Create resume linked to job
        resume_payload = {
            "title": "Resume Linked to Job",
            "target_job_id": job_id
        }
        status_res, res_draft, _ = self.make_request("/resumes", method="POST", data=resume_payload)
        self.assertEqual(status_res, 201)
        res_id = res_draft["id"]

        # Delete resume
        status_del, del_resp, _ = self.make_request(f"/resumes/{res_id}", method="DELETE")
        self.assertEqual(status_del, 200)

        # Confirm resume is 404
        status_check, _, _ = self.make_request(f"/resumes/{res_id}")
        self.assertEqual(status_check, 404)

        # Confirm job STILL EXISTS
        status_job_check, job_fetched, _ = self.make_request(f"/applications/{job_id}")
        self.assertEqual(status_job_check, 200)
        self.assertEqual(job_fetched["company_name"], "PreservedCompany")

    def test_06_explainable_quality_review(self):
        """Verify the rule-based ATS quality review flags missing info, action verbs, and vague phrases."""
        # Resume with incomplete contact info and vague phrasing
        flawed_payload = {
            "title": "Review Test Resume",
            "contact_info": {
                "full_name": "",  # Missing name!
                "email": "invalid-email-format",  # Invalid email!
                "phone": ""
            },
            "summary": "Lorem ipsum dolor sit amet",
            "projects": [
                {
                    "title": "Inventory Management",
                    "technologies": [],  # Missing tech tags
                    "bullets": [
                        "Worked on the backend using Python.",  # Vague phrase: 'worked on'
                        "Responsible for maintaining database tables."  # Vague phrase: 'responsible for'
                    ]
                }
            ]
        }
        _, created, _ = self.make_request("/resumes", method="POST", data=flawed_payload)
        res_id = created["id"]

        status_rev, review, _ = self.make_request(f"/resumes/{res_id}/review", method="POST")
        self.assertEqual(status_rev, 200)
        self.assertIn("overall_score", review)
        self.assertLess(review["overall_score"], 60)  # Flawed resume should have low score
        self.assertIn("score_breakdown", review)

        crit_rules = [iss["rule_id"] for iss in review.get("critical_issues", [])]
        self.assertIn("missing_name", crit_rules)
        self.assertIn("invalid_email", crit_rules)

        # Check bullet phrasing analysis
        insights = review.get("bullet_insights", [])
        self.assertTrue(any(i.get("has_vague_phrase") for i in insights))

    def test_07_job_specific_tailoring(self):
        """Verify keyword matching compares resume content to saved job requirements."""
        # Create job with specific description
        job_payload = {
            "company_name": "CloudScale AI",
            "job_title": "Full-Stack Software Engineer",
            "job_description": "We are seeking a Full-Stack Engineer skilled in React, TypeScript, FastAPI, PostgreSQL, and Docker containerization."
        }
        _, job, _ = self.make_request("/applications", method="POST", data=job_payload)
        job_id = job["id"]

        # Create resume mentioning React and FastAPI, but missing Docker and PostgreSQL
        resume_payload = {
            "title": "Tailoring Candidate",
            "skills": [
                {"category": "Frontend", "items": ["React", "JavaScript"]},
                {"category": "Backend", "items": ["FastAPI", "Python"]}
            ],
            "projects": [
                {
                    "title": "Web App",
                    "technologies": ["React", "FastAPI"],
                    "bullets": ["Developed user interface with React."]
                }
            ]
        }
        _, resume, _ = self.make_request("/resumes", method="POST", data=resume_payload)
        res_id = resume["id"]

        status_tailor, tailor_res, _ = self.make_request(f"/resumes/{res_id}/tailor/{job_id}", method="POST")
        self.assertEqual(status_tailor, 200)
        self.assertIn("keyword_match_percentage", tailor_res)
        self.assertGreater(tailor_res["keyword_match_percentage"], 0)

        present_kws = [k["keyword"].lower() for k in tailor_res.get("present_keywords", [])]
        self.assertIn("react", present_kws)
        self.assertIn("fastapi", present_kws)

        # Check suggestions
        suggestions = tailor_res.get("truthful_alignment_suggestions", [])
        self.assertTrue(len(suggestions) > 0)

    def test_08_docx_export_openxml_validity(self):
        """Verify the .docx export generates a genuine Microsoft Word OpenXML file with candidate text."""
        resume_payload = {
            "title": "Word Export Validation Resume",
            "contact_info": {
                "full_name": "Morgan Freeman",
                "email": "morgan.f@example.org",
                "phone": "+1 555-4321",
                "location": "New York, NY"
            },
            "summary": "Accomplished software engineer with comprehensive full-stack expertise.",
            "skills": [
                {"category": "Core Stack", "items": ["Python", "FastAPI", "React", "PostgreSQL"]}
            ],
            "projects": [
                {
                    "title": "Autonomous Agent Engine",
                    "technologies": ["Python", "FastAPI"],
                    "bullets": ["Architected distributed task dispatch system handling 10,000 req/sec."]
                }
            ]
        }
        _, resume, _ = self.make_request("/resumes", method="POST", data=resume_payload)
        res_id = resume["id"]

        status_export, docx_bytes, headers = self.make_request(f"/resumes/{res_id}/export/docx")
        self.assertEqual(status_export, 200)
        self.assertTrue(len(docx_bytes) > 500, "DOCX file is suspiciously small")

        # Test valid OpenXML zip archive structure
        with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as z:
            namelist = z.namelist()
            self.assertIn("word/document.xml", namelist)
            self.assertIn("[Content_Types].xml", namelist)
            self.assertIn("word/_rels/document.xml.rels", namelist)

            # Inspect document.xml content
            doc_xml = z.read("word/document.xml").decode("utf-8")
            self.assertIn("Morgan Freeman", doc_xml)
            self.assertIn("Accomplished software engineer", doc_xml)
            self.assertIn("Autonomous Agent Engine", doc_xml)
            self.assertIn("Architected distributed task dispatch system", doc_xml)

    def test_09_sample_resume_endpoint(self):
        """Verify the sample template returns standard student resume structure."""
        status, sample, _ = self.make_request("/resumes/sample?role=frontend")
        self.assertEqual(status, 200)
        self.assertIn("title", sample)
        self.assertIn("contact_info", sample)
        self.assertIn("skills", sample)
        self.assertIn("projects", sample)
        self.assertIn("education", sample)
        self.assertTrue(len(sample["skills"]) > 0)

    def test_10_missing_records_return_404(self):
        """Verify non-existent resume ID returns 404."""
        status, err, _ = self.make_request("/resumes/999999")
        self.assertEqual(status, 404)

        status_del, _, _ = self.make_request("/resumes/999999", method="DELETE")
        self.assertEqual(status_del, 404)

        status_rev, _, _ = self.make_request("/resumes/999999/review", method="POST")
        self.assertEqual(status_rev, 404)


if __name__ == "__main__":
    unittest.main()
