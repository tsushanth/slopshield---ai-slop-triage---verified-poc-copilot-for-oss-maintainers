#!/bin/sh
# Repro for the reflected-XSS bug in /greet: an unescaped <script> tag
# should come back verbatim in the response body.
set -e

python3 app.py &
APP_PID=$!
trap 'kill $APP_PID 2>/dev/null || true' EXIT

for i in 1 2 3 4 5; do
  sleep 1
  curl -sf http://127.0.0.1:5000/greet?name=x >/dev/null 2>&1 && break
done

PAYLOAD='<script>alert(1)</script>'
RESPONSE=$(curl -s "http://127.0.0.1:5000/greet" --get --data-urlencode "name=$PAYLOAD")
echo "response body: $RESPONSE"

if echo "$RESPONSE" | grep -qF "$PAYLOAD"; then
  echo "REPRO_RESULT: PASS"
  exit 0
else
  echo "REPRO_RESULT: FAIL"
  exit 1
fi
