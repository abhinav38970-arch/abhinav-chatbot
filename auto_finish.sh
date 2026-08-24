#!/bin/bash
# Auto-finisher v3 — the complete overnight chain, zero human input:
#   0. Wait for main crawl (PID $1)
#   1. Top-up pipeline pass: ALL discovered PDFs + fixed-slug schools
#      (msjhs/msje/green) + preschool/vista/rix-glankler real URLs + stragglers
#   2. Rebuild FAISS vector index over all chunks
#   3. Run FULL overnight checks: data coverage per school,
#      parent/student/teacher retrieval questions, guardrail attacks,
#      PII redaction, end-to-end safety
#   4. Final summary

set -u
cd "$(dirname "$0")"
MAIN_PID="$1"

echo "$(date) [watcher] Waiting for main crawl PID $MAIN_PID..."
while kill -0 "$MAIN_PID" 2>/dev/null; do
    sleep 30
done

echo "$(date) [1/3] Starting top-up pipeline pass..."
python3 -c "
from backend.app.scraper.pipeline import run_pipeline
run_pipeline()
" >> topup_run.log 2>&1
echo "$(date) [1/3] Top-up done (details in topup_run.log)."

echo "$(date) [2/3] Rebuilding FAISS index..."
python3 -c "
from backend.app.retrieval.indexer import build_index
build_index()
" >> topup_run.log 2>&1
echo "$(date) [2/3] Index rebuilt."

echo "$(date) [3/3] Running FULL overnight verification suite..."
python3 run_overnight_checks.py > overnight_checks.log 2>&1
CHECK_EXIT=$?
tail -40 overnight_checks.log
[ $CHECK_EXIT -eq 0 ] && echo "$(date) ✅ All overnight checks PASSED" \
                      || echo "$(date) ⚠️ Some checks failed - see overnight_checks.log"

echo "$(date) FINAL DATA SUMMARY:"
python3 - <<'EOF'
import sqlite3
db = sqlite3.connect("backend/app/school_data.db")
q = lambda sql: db.execute(sql).fetchone()[0]
pdfs = q("SELECT COUNT(*) FROM pages WHERE page_type = 'pdf'")
tables = q("SELECT COUNT(*) FROM chunks WHERE content LIKE '| %'")
contacts = q("SELECT COUNT(*) FROM chunks WHERE content LIKE '%@fusdk12%' OR content GLOB '*[0-9][0-9][0-9]-[0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]*'")
print(f"Pages: {q('SELECT COUNT(*) FROM pages')} | Chunks: {q('SELECT COUNT(*) FROM chunks')} | "
      f"PDFs: {pdfs} | Schools covered: {q('SELECT COUNT(DISTINCT school_id) FROM pages')} | "
      f"Table chunks: {tables} | Contact chunks: {contacts}")
EOF
echo "$(date) Done. Push to GitHub + restart the app and you're live. ☀️"
