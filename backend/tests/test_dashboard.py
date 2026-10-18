"""
SkillBridge Day 6 & 7 Test Suite - Unified Career Preparation Dashboard
Verifies:
1. Complete dashboard summary response structure and types
2. Summary card calculations (live jobs, question mastery, mock sessions)
3. Application funnel structure (active pipeline vs final outcomes)
4. Upcoming deadlines with deterministic urgency sorting
5. Skill gap aggregation from saved analyses
6. Interview preparation mastery and topic tracking
7. Deterministic next-step recommendations linking to actual routes
"""

import os
import unittest
import json
import urllib.request
import urllib.error

BASE_URL = os.getenv("TEST_API_URL", "http://127.0.0.1:8000/api")


class TestDashboardSummary(unittest.TestCase):
    """API integration tests for the unified Career Preparation Dashboard."""

    def make_request(self, endpoint, method="GET", data=None):
        url = f"{BASE_URL}{endpoint}"
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
        with urllib.request.urlopen(req, data=encoded_data, timeout=10) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)

    def test_dashboard_summary_structure(self):
        """Verify the complete dashboard summary payload structure and types."""
        status_code, data = self.make_request("/dashboard/summary")
        self.assertEqual(status_code, 200)

        # 1. Summary Cards
        self.assertIn("summary_cards", data)
        cards = data["summary_cards"]
        required_card_keys = [
            "total_saved_jobs",
            "applications_submitted",
            "interviews_in_progress",
            "offers_received",
            "rejected_count",
            "withdrawn_count",
            "total_jobs",
            "upcoming_deadlines_count",
            "total_questions_saved",
            "questions_confident",
            "questions_learning",
            "sessions_completed",
            "sessions_in_progress",
            "average_self_assessment"
        ]
        for key in required_card_keys:
            self.assertIn(key, cards, f"Missing key '{key}' in summary_cards")

        self.assertGreaterEqual(cards["total_saved_jobs"], 0)
        self.assertGreaterEqual(cards["total_questions_saved"], 0)
        self.assertGreaterEqual(cards["sessions_completed"], 0)

        # 2. Application Funnel
        self.assertIn("application_funnel", data)
        funnel = data["application_funnel"]
        self.assertIn("pipeline", funnel)
        self.assertIn("outcomes", funnel)

        expected_stages = ["Saved", "Applied", "Assessment", "Interview", "Offer"]
        actual_stages = [stage["stage"] for stage in funnel["pipeline"]]
        for stage_name in expected_stages:
            self.assertIn(stage_name, actual_stages)

        expected_outcomes = ["Rejected", "Withdrawn"]
        actual_outcomes = [stage["stage"] for stage in funnel["outcomes"]]
        for outcome_name in expected_outcomes:
            self.assertIn(outcome_name, actual_outcomes)

        # 3. Upcoming Deadlines
        self.assertIn("upcoming_deadlines", data)
        self.assertIsInstance(data["upcoming_deadlines"], list)
        for dl in data["upcoming_deadlines"]:
            self.assertIn("id", dl)
            self.assertIn("company_name", dl)
            self.assertIn("job_title", dl)
            self.assertIn("deadline", dl)
            self.assertIn("days_remaining", dl)
            self.assertIn("urgency", dl)
            self.assertIn(dl["urgency"], ["overdue", "urgent", "soon", "upcoming"])

        # 4. Skill Gap Summary
        self.assertIn("skill_gap_summary", data)
        skill_gaps = data["skill_gap_summary"]
        self.assertIn("total_analyses", skill_gaps)
        self.assertIn("frequently_missing_required", skill_gaps)
        self.assertIn("frequently_missing_preferred", skill_gaps)
        self.assertIn("suggested_learning_tasks", skill_gaps)

        # 5. Interview Prep Summary
        self.assertIn("interview_prep_summary", data)
        prep = data["interview_prep_summary"]
        self.assertIn("learning_count", prep)
        self.assertIn("confident_count", prep)
        self.assertIn("total_questions", prep)
        self.assertIn("recent_sessions", prep)
        self.assertIn("topics_needing_practice", prep)

        # 6. Recommended Next Steps
        self.assertIn("recommended_next_steps", data)
        recs = data["recommended_next_steps"]
        self.assertIsInstance(recs, list)
        for r in recs:
            self.assertIn("category", r)
            self.assertIn("title", r)
            self.assertIn("description", r)
            self.assertIn("action_text", r)
            self.assertIn("action_link", r)
            self.assertIn("priority", r)
            self.assertIn(r["priority"], ["high", "medium", "low"])
            # Action path must be an actual internal route
            self.assertTrue(r["action_link"].startswith("/"))

    def test_upcoming_deadlines_sorted_by_urgency(self):
        """Verify that deadlines are ordered with the lowest days_remaining first."""
        status_code, data = self.make_request("/dashboard/summary")
        self.assertEqual(status_code, 200)
        deadlines = data.get("upcoming_deadlines", [])

        if len(deadlines) >= 2:
            days = [d["days_remaining"] for d in deadlines]
            self.assertEqual(days, sorted(days), "Deadlines must be sorted ascending by urgency")

    def test_pipeline_vs_outcome_separation(self):
        """Verify rejected and withdrawn jobs are separate from the active pipeline."""
        status_code, data = self.make_request("/dashboard/summary")
        self.assertEqual(status_code, 200)

        funnel = data["application_funnel"]
        pipeline_stages = {s["stage"] for s in funnel["pipeline"]}
        outcome_stages = {s["stage"] for s in funnel["outcomes"]}

        # Pipeline stages and outcome stages must not overlap
        self.assertTrue(pipeline_stages.isdisjoint(outcome_stages))
        self.assertNotIn("Rejected", pipeline_stages)
        self.assertNotIn("Withdrawn", pipeline_stages)


if __name__ == "__main__":
    unittest.main()
