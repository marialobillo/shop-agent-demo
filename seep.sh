#!/bin/bash
URL="https://apply.caplena.com/api-guru"

texts=(
  "The Internet?  We are not interested in it."
  "The Internet? We are not interested in it."
  "The Internet? We are interested in it."
  "The Internet?  We are not interested in it"
)
fields=(message answer b64 text quote decoded key)

try() {
  local desc="$1"; shift
  local body
  body=$(curl -s -X POST "$@" "$URL")
  if [[ "$body" != "That's not correct" && "$body" != *"decode this message"* ]]; then
    echo "=== HIT: $desc ==="
    echo "$body"
    echo "================="
  fi
}

for t in "${texts[@]}"; do
  b64=$(echo -n "$t" | base64)
  # texto plano y base64, como raw text/plain
  try "raw plain: $t"  -H "Content-Type: text/plain" --data-raw "$t"
  try "raw b64:  $t"   -H "Content-Type: text/plain" --data-raw "$b64"
  for f in "${fields[@]}"; do
    try "json $f plain: $t" -H "Content-Type: application/json" -d "{\"$f\":\"$t\"}"
    try "json $f b64:   $t" -H "Content-Type: application/json" -d "{\"$f\":\"$b64\"}"
  done
done
echo "Barrido terminado."