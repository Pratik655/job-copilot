from __future__ import annotations

import argparse
import json
import sys

import uvicorn

from jobcopilot.db import connect, export_jobs_data, init_db
from jobcopilot.ingest import ingest_inbox, ingest_paste, ingest_watchlist
from jobcopilot.pipeline import process_new_jobs, rescore_all_jobs, run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="jobcopilot",
        description="Advanced Job Copilot - B.Tech CSE & Multi-City Indian Tech Edition",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ingest", help="Pull public ATS watchlist + inbox files")
    sub.add_parser("score", help="Score and draft packets for new jobs")
    sub.add_parser("rescore", help="Re-score all jobs against updated B.Tech CSE profile and multi-city filters")
    sub.add_parser("run", help="Ingest, score, and draft")
    serve = sub.add_parser("serve", help="Open the modern review UI")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)

    paste = sub.add_parser("paste", help="Ingest a pasted job description")
    paste.add_argument("file", nargs="?", help="Path to a .md/.txt file; otherwise stdin")
    paste.add_argument("--url", default=None)

    sub.add_parser("stats", help="Show current job pipeline breakdown and statistics")
    export_cmd = sub.add_parser("export", help="Export jobs data (CSV or JSON)")
    export_cmd.add_argument("--status", default=None, help="Filter by status (e.g. queued, ready, applied)")
    export_cmd.add_argument("--format", choices=["csv", "json"], default="csv")
    export_cmd.add_argument("--out", default=None, help="Output file path (default stdout)")

    args = parser.parse_args(argv)
    init_db()

    if args.cmd == "stats":
        from jobcopilot.db import counts, get_available_filters
        with connect() as conn:
            c = counts(conn)
            f = get_available_filters(conn)
        print("\n=== JOB COPILOT STATUS ===")
        for status_name, cnt in c.items():
            print(f"  {status_name.capitalize():<12}: {cnt}")
        print("\n=== DOMAIN BREAKDOWN ===")
        for d in f.get("domains", []):
            print(f"  {d['label']:<26}: {d['count']}")
        print("\n=== TOP CITIES ===")
        for ci in f.get("cities", [])[:8]:
            print(f"  {ci['city']:<22}: {ci['count']}")
        return 0
    if args.cmd == "ingest":
        print(json.dumps({"ats": ingest_watchlist(), "inbox": ingest_inbox()}, indent=2))
        return 0
    if args.cmd == "score":
        print(json.dumps(process_new_jobs(), indent=2))
        return 0
    if args.cmd == "rescore":
        print(json.dumps(rescore_all_jobs(), indent=2))
        return 0
    if args.cmd == "run":
        print(json.dumps(run_pipeline(), indent=2))
        return 0
    if args.cmd == "export":
        with connect() as conn:
            data = export_jobs_data(conn, status=args.status, fmt=args.format)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(data)
            print(f"Exported to {args.out}")
        else:
            print(data)
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
