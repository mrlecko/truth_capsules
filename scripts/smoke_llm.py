#!/usr/bin/env python3
# Minimal stub: write tiny 'live' artifacts (no real API calls).
import argparse, json, os
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
json.dump({"items":[{"answer":"Paris is the capital of France.","citations":[{"url":"https://en.wikipedia.org/wiki/Paris"}], "abstained": False}]}, open(os.path.join(args.out,"answers.json"),"w"))
json.dump({"items":[{"name":"book_meeting","args":{"title":"Sync","start_iso":"2025-11-07T15:00:00Z","duration_min":30}}]}, open(os.path.join(args.out,"tool_calls.json"),"w"))
json.dump({"items":[{"plan":["Search docs"],"verification_evidence":["DOC-123"],"final_answer":"Per DOC-123, enabled."}]}, open(os.path.join(args.out,"pva_logs.json"),"w"))
json.dump({"text":"Contact support at [redacted email]"}, open(os.path.join(args.out,"pii_scan.json"),"w"))
json.dump({"question":"?","answer":"Paris is the capital of France.","citations":[{"url":"https://en.wikipedia.org/wiki/Paris"}]}, open(os.path.join(args.out,"answer_candidate.json"),"w"))
print("Smoke artifacts written.")
