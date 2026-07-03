#!/usr/bin/env bash
# Smoke-test the running API. Start the server first:
#   uvicorn api.app:app --host 127.0.0.1 --port 8000
set -e
BASE=http://127.0.0.1:8000

echo "=== Ingest text ==="
curl -s -X POST $BASE/ingest/text \
  -H "Content-Type: application/json" \
  -d '{"source_id":"memo-1","text":"Berlin is the capital of Germany.","source_metadata":{"source_type":"news_article"}}' | python3 -m json.tool

echo ""
echo "=== Ingest table ==="
curl -s -X POST $BASE/ingest/table \
  -H "Content-Type: application/json" \
  -d '{"source_id":"q3-table","rows":[{"quarter":"Q3","revenue":"8"}],"source_metadata":{"source_type":"official_table"}}' | python3 -m json.tool

echo ""
echo "=== Query ==="
curl -s -X POST $BASE/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the capital of Germany?","budget":512}' | python3 -m json.tool

echo ""
echo "=== Verify/Generate with fault inject ==="
curl -s -X POST $BASE/verify/generate \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What was revenue in Q3?",
    "fault_inject": true,
    "evidence_sources": [{"source_name":"Q3 Official","source_type":"official_table","table":[{"quarter":"Q3","revenue":"8"}]}]
  }' | python3 -m json.tool

echo ""
echo "=== Paper search ==="
curl -s -X POST $BASE/papers/search \
  -H "Content-Type: application/json" \
  -d '{"topic":"hallucination detection","use_demo_fallback":true}' | python3 -m json.tool

echo ""
echo "Done."
