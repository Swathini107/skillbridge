#!/usr/bin/env bash
# ==============================================================================
# SkillBridge Isolated Test Runner
# Runs the automated test suite against an isolated temporary test database.
# Ensures zero pollution or modification of the development/demo database.
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

TEST_DB="test_skillbridge_isolated.db"
TEST_PORT=8005

echo "==> Preparing isolated test database: $TEST_DB"
# Remove any leftover previous test database
rm -f "$TEST_DB" "${TEST_DB}-shm" "${TEST_DB}-wal"

# If clean backup exists, copy it as the starting baseline, otherwise init_db will create schema
if [ -f "skillbridge_backup_clean.db" ]; then
    cp "skillbridge_backup_clean.db" "$TEST_DB"
    echo "==> Seeded test database from clean backup."
fi

echo "==> Starting isolated backend on port $TEST_PORT..."
DATABASE_URL="sqlite:///./$TEST_DB" venv/bin/uvicorn app.main:app --host 127.0.0.1 --port $TEST_PORT > /dev/null 2>&1 &
SERVER_PID=$!

# Ensure server cleanup on exit
cleanup() {
    echo "==> Shutting down test backend (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
    echo "==> Cleaning up $TEST_DB..."
    rm -f "$TEST_DB" "${TEST_DB}-shm" "${TEST_DB}-wal"
    echo "==> Cleanup complete."
}
trap cleanup EXIT

# Wait for server to become healthy
echo "==> Waiting for test backend to become ready..."
for i in {1..30}; do
    if curl -s "http://127.0.0.1:$TEST_PORT/api/health" | grep -q '"status":"ok"'; then
        echo "==> Test backend is online!"
        break
    fi
    sleep 0.2
done

# Run test suite with BASE_URL and DB pointing to isolated test server
echo "==> Running test suite against isolated environment..."
TEST_API_URL="http://127.0.0.1:$TEST_PORT/api" DATABASE_URL="sqlite:///./$TEST_DB" venv/bin/python -m unittest discover -s tests -p "test_*.py"

echo "==> All isolated tests executed successfully!"
