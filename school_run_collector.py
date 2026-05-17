#!/usr/bin/env python3
"""
School Run Traffic Collector
Runs every 5 minutes via launchd.
Collects drive times from home to school during:
  - Morning window:   7:00am – 10:00am (weekdays)
  - Afternoon window: 2:30pm –  5:00pm (weekdays)
Saves results to ~/Development/school-run-background-app/csv/school_run_data.csv

Configuration is via environment variables — see .env.example.
"""

import urllib.request
import urllib.parse
import json
import csv
import os
import sys
from datetime import datetime

# ── Configuration (from environment variables) ────────────────────────────────
API_KEY = os.environ.get("SCHOOL_RUN_API_KEY", "")
ORIGIN  = os.environ.get("SCHOOL_RUN_ORIGIN", "")
DEST    = os.environ.get("SCHOOL_RUN_DEST", "")
CSV_PATH = os.path.expanduser("~/Development/school-run-background-app/csv/school_run_data.csv")
LOG_PATH = os.path.expanduser("~/Development/school-run-background-app/logs/school_run.log")

# Collection windows (hour, minute) — inclusive start, exclusive end
WINDOWS = [
    (7, 0, 10, 0),    # Morning:   7:00am – 10:00am
    (14, 30, 17, 0),  # Afternoon: 2:30pm –  5:00pm
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def in_window(now):
    """Return True if 'now' falls within any collection window on a weekday."""
    if now.weekday() >= 5:   # 5=Saturday, 6=Sunday
        return False
    h, m = now.hour, now.minute
    total = h * 60 + m
    for (sh, sm, eh, em) in WINDOWS:
        start = sh * 60 + sm
        end   = eh * 60 + em
        if start <= total < end:
            return True
    return False


def fetch_routes(api_key, origin, destination, departure_time="now"):
    """Call Google Directions API and return list of route dicts."""
    params = {
        "origin":                   origin,
        "destination":              destination,
        "key":                      api_key,
        "alternatives":             "true",
        "departure_time":           departure_time,
        "traffic_model":            "best_guess",
    }
    url = "https://maps.googleapis.com/maps/api/directions/json?" + urllib.parse.urlencode(params)

    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    if data.get("status") != "OK":
        raise ValueError(f"API error: {data.get('status')} — {data.get('error_message','')}")

    routes = []
    for i, route in enumerate(data["routes"]):
        leg = route["legs"][0]
        duration_in_traffic = leg.get("duration_in_traffic", leg["duration"])
        routes.append({
            "rank":             i + 1,
            "summary":         route.get("summary", f"Route {i+1}"),
            "distance_km":     round(leg["distance"]["value"] / 1000, 2),
            "duration_min":    round(leg["duration"]["value"] / 60, 1),
            "traffic_min":     round(duration_in_traffic["value"] / 60, 1),
            "delay_min":       round((duration_in_traffic["value"] - leg["duration"]["value"]) / 60, 1),
        })

    # Sort by traffic duration so rank 1 = fastest right now
    routes.sort(key=lambda r: r["traffic_min"])
    for i, r in enumerate(routes):
        r["rank"] = i + 1

    return routes


def append_to_csv(timestamp, routes):
    """Write one row per route to the CSV (creates header if needed)."""
    file_exists = os.path.isfile(CSV_PATH)
    fieldnames = [
        "timestamp", "date", "time", "weekday",
        "rank", "summary",
        "distance_km", "duration_min", "traffic_min", "delay_min",
    ]
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists or os.path.getsize(CSV_PATH) == 0:
            writer.writeheader()
        for r in routes:
            writer.writerow({
                "timestamp":    timestamp.isoformat(),
                "date":         timestamp.strftime("%Y-%m-%d"),
                "time":         timestamp.strftime("%H:%M"),
                "weekday":      timestamp.strftime("%A"),
                "rank":         r["rank"],
                "summary":      r["summary"],
                "distance_km":  r["distance_km"],
                "duration_min": r["duration_min"],
                "traffic_min":  r["traffic_min"],
                "delay_min":    r["delay_min"],
            })


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    now = datetime.now()

    if not in_window(now):
        log(f"Outside collection window ({now.strftime('%A %H:%M')}) — skipping.")
        sys.exit(0)

    missing = [k for k, v in [("SCHOOL_RUN_API_KEY", API_KEY), ("SCHOOL_RUN_ORIGIN", ORIGIN), ("SCHOOL_RUN_DEST", DEST)] if not v]
    if missing:
        log(f"ERROR: Missing environment variables: {', '.join(missing)}. See .env.example.")
        sys.exit(1)

    log(f"Collecting routes at {now.strftime('%A %H:%M')} ...")

    try:
        routes = fetch_routes(API_KEY, ORIGIN, DEST)
        append_to_csv(now, routes)
        fastest = routes[0]
        log(f"  ✓ {len(routes)} routes saved. Fastest: {fastest['summary']} "
            f"({fastest['traffic_min']} min with traffic)")
    except Exception as e:
        log(f"  ✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
