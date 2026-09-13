#!/bin/sh
set -eu
COOKIE=/tmp/pc_cookies.txt
rm -f "$COOKIE"
HTML=$(curl -s -c "$COOKIE" http://127.0.0.1:8000/accounts/login/)
TOKEN=$(printf '%s\n' "$HTML" | sed -n 's/.*name="csrfmiddlewaretoken" value="\([^"]*\)".*/\1/p' | head -n1)
echo "csrf_len=${#TOKEN}"
CODE=$(curl -s -o /tmp/login_out.html -w "%{http_code}" -b "$COOKIE" -c "$COOKIE" \
  -X POST "http://127.0.0.1:8000/accounts/login/" \
  -H "Referer: http://127.0.0.1:8000/accounts/login/" \
  -H "Origin: http://127.0.0.1:8000" \
  --data-urlencode "csrfmiddlewaretoken=$TOKEN" \
  --data-urlencode "username=purohit_sharma" \
  --data-urlencode "password=password123")
echo "POST_CODE=$CODE"
echo "POST_REDIRECT_HINT=$(grep -i location /tmp/login_out.html | head -1 || true)"
# show title/errors
grep -Eo '<title>[^<]+</title>|Invalid|errorlist|CSRF|Dashboard|Welcome|alert' /tmp/login_out.html | head -20 || true
# follow redirect manually if 302 stored in headers
CODE2=$(curl -s -D /tmp/login_hdrs.txt -o /tmp/login_out2.html -w "%{http_code}" -b "$COOKIE" -c "$COOKIE" \
  -X POST "http://127.0.0.1:8000/accounts/login/" \
  -H "Referer: http://127.0.0.1:8000/accounts/login/" \
  -H "Origin: http://127.0.0.1:8000" \
  --data-urlencode "csrfmiddlewaretoken=$TOKEN" \
  --data-urlencode "username=purohit_sharma" \
  --data-urlencode "password=password123")
echo "POST2_CODE=$CODE2"
head -n 20 /tmp/login_hdrs.txt
LOC=$(sed -n 's/[Ll]ocation: //p' /tmp/login_hdrs.txt | tr -d '\r' | head -n1)
echo "LOC=$LOC"
if [ -n "$LOC" ]; then
  CODE3=$(curl -s -o /tmp/after.html -w "%{http_code} %{url_effective}" -b "$COOKIE" -L "http://127.0.0.1:8000$LOC")
  echo "AFTER=$CODE3"
  grep -Eo '<title>[^<]+</title>|Server Error|Traceback|Dashboard|Welcome' /tmp/after.html | head -20
fi
# purohit dashboard
CODE4=$(curl -s -o /tmp/pdash.html -w "%{http_code} %{url_effective}" -b "$COOKIE" -L http://127.0.0.1:8000/dashboard/purohit/)
echo "PDASH=$CODE4"
grep -Eo '<title>[^<]+</title>|Server Error|Traceback|Dashboard|Welcome|Bookings' /tmp/pdash.html | head -20