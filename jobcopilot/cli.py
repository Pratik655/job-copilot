from __future__ import annotations

import argparse
import json
import sys

import uvicorn

from jobcopilot.db import init_db
from jobcopilot.ingest import ingest_inbox, ingest_paste, ingest_watchlist
from jobcopilot.pipeline import process_new_jobs, run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jobcopilot", description="Review-first Bangalore job copilot")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ingest", help="Pull public ATS watchlist + inbox files")
    sub.add_parser("score", help="Score and draft packets for new jobs")
    sub.add_parser("run", help="Ingest, score, and draft")
    serve = sub.add_parser("serve", help="Open the review UI")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)

    paste = sub.add_parser("paste", help="Ingest a pasted job description")
    paste.add_argument("file", nargs="?", help="Path to a .md/.txt file; otherwise stdin")
    paste.add_argument("--url", default=None)

    args = parser.parse_args(argv)
    init_db()

    if args.cmd == "ingest":
        print(json.dumps({"ats": ingest_watchlist(), "inbox": ingest_inbox()}, indent=2))
        return 0
    if args.cmd == "score":
        print(json.dumps(process_new_jobs(), indent=2))
        return 0
    if args.cmd == "run":
        print(json.dumps(run_pipeline(), indent=2))
        return 0
    if args.cmd == "paste":
        text = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
        print(json.dumps(ingest_paste(text, args.url), indent=2))
        process_new_jobs()
        return 0
    if args.cmd == "serve":
        uvicorn.run("jobcopilot.web:app", host=args.host, port=args.port, reload=False)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
