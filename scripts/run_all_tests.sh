#!/usr/bin/env bash
set -e

echo "=========================================="
echo "  Social Media Platform - Running All Tests"
echo "=========================================="

echo ""
echo "--- Frontend Tests ---"
cd "$(dirname "$0")/../frontend"
npm run test -- --run 2>&1 || { echo "Frontend tests FAILED"; exit 1; }
echo "Frontend tests PASSED"

echo ""
echo "--- Admin Panel Tests ---"
cd "$(dirname "$0")/../frontend-admin"
npm run test -- --run 2>&1 || { echo "Admin tests FAILED"; exit 1; }
echo "Admin panel tests PASSED"

echo ""
echo "--- Backend Tests (via Docker) ---"
cd "$(dirname "$0")/.."
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit 2>&1 || { echo "Backend tests FAILED"; exit 1; }
echo "Backend tests PASSED"

echo ""
echo "=========================================="
echo "  All tests PASSED!"
echo "=========================================="
