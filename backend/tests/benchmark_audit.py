"""
SkillBridge Performance & Reliability Benchmark Audit Script
Measures actual API response times (median, p95, max), throughput, and error rates
across representative read, write, and export workflows.
"""

import time
import json
import statistics
import concurrent.futures
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000/api"


def make_http_call(endpoint, method="GET", data=None, timeout=10):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    encoded = json.dumps(data).encode("utf-8") if data is not None else None
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, data=encoded, timeout=timeout) as resp:
            body = resp.read()
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return True, resp.status, elapsed_ms, len(body)
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return False, e.code, elapsed_ms, 0
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return False, 500, elapsed_ms, 0


def benchmark_endpoint(name, endpoint, method="GET", data=None, iterations=30):
    latencies = []
    errors = 0
    # Warmup
    make_http_call(endpoint, method, data)

    for _ in range(iterations):
        success, status, elapsed, _ = make_http_call(endpoint, method, data)
        if success and status in (200, 201):
            latencies.append(elapsed)
        else:
            errors += 1

    if not latencies:
        return {
            "name": name,
            "count": iterations,
            "errors": errors,
            "median_ms": None,
            "p95_ms": None,
            "mean_ms": None,
            "max_ms": None
        }

    latencies.sort()
    p95_idx = int(0.95 * len(latencies))
    p95_val = latencies[min(p95_idx, len(latencies) - 1)]

    return {
        "name": name,
        "count": iterations,
        "errors": errors,
        "median_ms": round(statistics.median(latencies), 2),
        "p95_ms": round(p95_val, 2),
        "mean_ms": round(statistics.mean(latencies), 2),
        "max_ms": round(max(latencies), 2)
    }


def run_concurrency_load_test(endpoint, concurrency=10, total_requests=100):
    start = time.perf_counter()
    latencies = []
    errors = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(make_http_call, endpoint, "GET", None) for _ in range(total_requests)]
        for f in concurrent.futures.as_completed(futures):
            success, status, elapsed, _ = f.result()
            if success and status == 200:
                latencies.append(elapsed)
            else:
                errors += 1

    total_time = time.perf_counter() - start
    rps = round(total_requests / total_time, 1)

    latencies.sort()
    p95_idx = int(0.95 * len(latencies)) if latencies else 0
    p95_val = latencies[min(p95_idx, len(latencies) - 1)] if latencies else None

    return {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "duration_sec": round(total_time, 2),
        "requests_per_sec": rps,
        "errors": errors,
        "error_rate_pct": round((errors / total_requests) * 100, 2),
        "median_ms": round(statistics.median(latencies), 2) if latencies else None,
        "p95_ms": round(p95_val, 2) if p95_val else None
    }


if __name__ == "__main__":
    print("=" * 60)
    print("SKILLBRIDGE PERFORMANCE AUDIT — LATENCY BENCHMARK")
    print("=" * 60)

    # 1. First get a valid resume ID for resume endpoints
    success, status, _, body = make_http_call("/resumes")
    resume_id = 1
    if success:
        try:
            req = urllib.request.Request(f"{BASE_URL}/resumes")
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                if data:
                    resume_id = data[0]["id"]
        except Exception:
            pass

    test_endpoints = [
        ("Health Check", "/health", "GET", None),
        ("Dashboard Summary (Aggregated)", "/dashboard/summary", "GET", None),
        ("Application Tracker List", "/applications", "GET", None),
        ("Application Tracker Stats", "/applications/stats", "GET", None),
        ("Application Search Filter", "/applications?search=Engineer", "GET", None),
        ("Interview Questions List", "/questions", "GET", None),
        ("Interview Question Stats", "/questions/stats", "GET", None),
        ("Interview Questions Filter", "/questions?round_type=Technical", "GET", None),
        ("Practice Sessions List", "/practice/sessions", "GET", None),
        ("Resume List", "/resumes", "GET", None),
        ("Single Resume Fetch", f"/resumes/{resume_id}", "GET", None),
        ("Resume Quality Review", f"/resumes/{resume_id}/review", "POST", None),
        ("Resume DOCX Export", f"/resumes/{resume_id}/export/docx", "GET", None),
    ]

    results = []
    for name, ep, m, d in test_endpoints:
        r = benchmark_endpoint(name, ep, m, d, iterations=30)
        results.append(r)
        print(f"[{r['name']}] Median: {r['median_ms']} ms | p95: {r['p95_ms']} ms | Max: {r['max_ms']} ms | Errors: {r['errors']}")

    print("\n" + "=" * 60)
    print("CONCURRENCY STRESS LOAD TEST (Dashboard Summary)")
    print("=" * 60)

    for c in [1, 5, 10, 20]:
        load_res = run_concurrency_load_test("/dashboard/summary", concurrency=c, total_requests=100)
        print(f"Concurrency {c:2d} | Throughput: {load_res['requests_per_sec']:5.1f} req/s | Median: {load_res['median_ms']:5.1f} ms | p95: {load_res['p95_ms']:5.1f} ms | Errors: {load_res['errors']}")
