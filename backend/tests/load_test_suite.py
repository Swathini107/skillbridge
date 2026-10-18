"""
SkillBridge Realistic Multi-Module Load Testing Suite
Audits realistic read and write operations under increasing concurrency (1, 5, 10, 20).
Operations tested:
- Read: Dashboard Summary (Aggregated multi-table metrics)
- Read: Application Search & Filter (Job Tracker)
- Read: Interview Memory Bank Filter
- Write: Job Description Analyzer (NLP keyword & skill extraction, match scoring)
- Write: Practice Session Answer Auto-Save (Real transactional persistence)
"""

import time
import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

BASE_URL = "http://127.0.0.1:8000/api"

SAMPLE_JD = """
We are looking for a Junior Backend Developer proficient in Python, FastAPI, and SQL.
Experience with REST APIs, Git, Docker, and PostgreSQL is required.
Familiarity with React, AWS, or unit testing is a plus. Strong problem solving skills.
"""

def make_http_request(endpoint, method="GET", data=None, timeout=10):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, data=encoded_data, timeout=timeout) as response:
            body = response.read()
            elapsed_ms = (time.perf_counter() - start) * 1000
            return True, elapsed_ms, response.status, body
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return False, elapsed_ms, e.code, str(e)
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return False, elapsed_ms, 599, str(e)


def setup_temp_practice_session():
    """Create a temporary practice session for write tests."""
    payload = {
        "session_name": "Audit Load Test Session",
        "target_company": "Benchmark Corp",
        "target_role": "Software Engineer",
        "round_type": "Technical",
        "question_source": "Custom Input",
        "custom_questions": [
            {
                "question_text": "Explain database indexing and WAL mode benefits in SQLite.",
                "round_type": "Technical",
                "difficulty": "Intermediate",
                "expected_answer": "WAL mode enables concurrent reads without write locks."
            }
        ]
    }
    success, _, _, body = make_http_request("/practice/sessions", method="POST", data=payload)
    if success:
        session = json.loads(body.decode("utf-8"))
        session_id = session["id"]
        answer_id = session["answers"][0]["id"]
        return session_id, answer_id
    return None, None


def teardown_temp_practice_session(session_id):
    """Clean up the temporary session."""
    if session_id:
        make_http_request(f"/practice/sessions/{session_id}", method="DELETE")


def run_workload_worker(task_type, session_id=None, answer_id=None):
    if task_type == "dashboard":
        return make_http_request("/dashboard/summary")
    elif task_type == "applications":
        return make_http_request("/applications?search=engineer&status=Applied")
    elif task_type == "questions":
        return make_http_request("/questions?round_type=Technical&review_status=New")
    elif task_type == "analyzer":
        return make_http_request("/analyzer/analyze", method="POST", data={
            "job_description": SAMPLE_JD,
            "resume_or_profile_text": "Python, SQL, REST APIs, Git",
            "save_analysis": False
        })
    elif task_type == "save_answer" and session_id and answer_id:
        return make_http_request(f"/practice/sessions/{session_id}/answers/{answer_id}", method="PUT", data={
            "answer_text": "Continuous autosave test answer verifying transactional integrity.",
            "is_attempted": True,
            "time_spent_seconds": 15
        })
    return make_http_request("/health")


def execute_concurrency_test(concurrency_level, total_requests, session_id, answer_id):
    # Balanced mix: 35% dashboard, 25% applications, 20% questions, 10% analyzer, 10% answer save
    workload_tasks = []
    task_types = ["dashboard", "applications", "questions", "analyzer", "save_answer"]
    weights = [0.35, 0.25, 0.20, 0.10, 0.10]

    for i in range(total_requests):
        t = task_types[i % len(task_types)]
        workload_tasks.append(t)

    latencies = []
    errors = 0
    timeouts = 0

    start_wall = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency_level) as executor:
        futures = [
            executor.submit(run_workload_worker, t, session_id, answer_id)
            for t in workload_tasks
        ]
        for f in as_completed(futures):
            success, elapsed_ms, code, _ = f.result()
            latencies.append(elapsed_ms)
            if not success:
                errors += 1
                if code == 599:
                    timeouts += 1

    total_duration = time.perf_counter() - start_wall
    throughput = len(latencies) / total_duration if total_duration > 0 else 0

    return {
        "concurrency": concurrency_level,
        "total_requests": len(latencies),
        "throughput": round(throughput, 1),
        "median_ms": round(statistics.median(latencies), 2),
        "p95_ms": round(sorted(latencies)[min(int(len(latencies) * 0.95), len(latencies) - 1)], 2),
        "min_ms": round(min(latencies), 2),
        "max_ms": round(max(latencies), 2),
        "errors": errors,
        "error_rate": round((errors / len(latencies)) * 100, 2),
        "timeouts": timeouts
    }


def main():
    print("=" * 70)
    print("SKILLBRIDGE REALISTIC MULTI-MODULE LOAD BENCHMARK")
    print("=" * 70)
    print("Operations Mix: Dashboard reads, App search, Question filters,")
    print("                JD analysis, & Mock answer persistence.")
    print("Target Environment: Localhost (Mac Apple Silicon / Python 3.14 / SQLite WAL)")
    print("-" * 70)

    session_id, answer_id = setup_temp_practice_session()
    print(f"Created isolated test practice session: #{session_id}")

    try:
        concurrency_levels = [1, 5, 10, 20]
        results = []

        for c in concurrency_levels:
            total_reqs = 40 if c <= 5 else 60
            res = execute_concurrency_test(c, total_reqs, session_id, answer_id)
            results.append(res)
            print(f"Concurrency {res['concurrency']:2d} | "
                  f"Throughput: {res['throughput']:5.1f} req/s | "
                  f"Median: {res['median_ms']:6.2f} ms | "
                  f"p95: {res['p95_ms']:7.2f} ms | "
                  f"Max: {res['max_ms']:7.2f} ms | "
                  f"Errors: {res['errors']} ({res['error_rate']}%)")

        print("=" * 70)
        print("SUMMARY TABLE FOR REPORT:")
        print("Concurrency | Requests | Throughput | Median Latency | p95 Latency | Errors")
        print("-" * 70)
        for r in results:
            print(f"{r['concurrency']:11d} | {r['total_requests']:8d} | {r['throughput']:8.1f} r/s | {r['median_ms']:11.2f} ms | {r['p95_ms']:8.2f} ms | {r['errors']:6d} ({r['error_rate']}%)")
        print("=" * 70)

    finally:
        teardown_temp_practice_session(session_id)
        print("Cleaned up isolated practice session.")

if __name__ == "__main__":
    main()
