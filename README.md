# School Run Traffic Tracker

A lightweight macOS background service that collects real-time Google Maps route data for a home-to-school journey twice a day, every weekday. Data is saved to CSV so you can analyse which route and departure time consistently gets you there fastest.

---

## How It Works

A Python script runs every 5 minutes via macOS **launchd** (the built-in task scheduler). During the configured morning and afternoon windows it calls the Google Maps Directions API, captures travel times for all available routes, and appends a row per route to a CSV file.

```
launchd (every 5 min)
    └── school_run_collector.py
            └── Google Maps Directions API
                    └── csv/school_run_data.csv
```

### Collection windows

| Window | Time |
|---|---|
| Morning (drop-off) | 7:00am – 10:00am, weekdays |
| Afternoon (pick-up) | 2:30pm – 5:00pm, weekdays |

### Data collected per snapshot

| Field | Description |
|---|---|
| `timestamp` | ISO datetime of collection |
| `date` / `time` / `weekday` | Broken-out date parts for easy filtering |
| `rank` | 1 = fastest route at that moment |
| `summary` | Route name from Google Maps (e.g. "S Spencer St") |
| `distance_km` | Route distance in kilometres |
| `duration_min` | Google's no-traffic estimate |
| `traffic_min` | Actual estimated travel time with live traffic |
| `delay_min` | `traffic_min − duration_min` (traffic overhead) |

---

## Setup

### Prerequisites

- macOS (uses launchd)
- Python 3 (pre-installed on macOS)
- A [Google Maps Directions API key](https://console.cloud.google.com/) with the **Directions API** enabled

### 1. Clone the repo

```bash
git clone https://github.com/kristiandermody/school-run-background-app.git
cd school-run-background-app
```

### 2. Configure your environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your three values:

```
SCHOOL_RUN_API_KEY=AIza...your_key...
SCHOOL_RUN_ORIGIN=123 Home Street, Your City, State ZIP
SCHOOL_RUN_DEST=456 School Ave, Your City, State ZIP
```

> `.env` is gitignored and never committed — your key and address stay private.

### 3. Run the installer

```bash
bash install.sh
```

The installer will:
1. Detect your Python path
2. Copy the collector script to `SchoolRun/`
3. Write a launchd plist to `~/Library/LaunchAgents/` with your config injected
4. Load the service so it starts immediately and runs at every login
5. Fire one test collection to confirm everything works

### Uninstall

```bash
launchctl unload ~/Library/LaunchAgents/com.schoolrun.collector.plist
```

---

## Data & Analysis

After a few weeks of collection the CSV contains enough data to draw reliable conclusions about the best route and departure time for your specific journey.

### What the data showed (Las Vegas → Henderson route, May 6–15 2026)

Over **999 data points across 8 school days and 6 candidate routes**, the analysis produced two clear recommendations — and the winning route is different each way.

#### Morning drop-off

| Route | Avg Travel | Worst Ever | Ranked #1 |
|---|---|---|---|
| **S Spencer St** | **20.2 min** | **20.8 min** | **100%** |
| S Eastern Ave | 22.1 min | 22.2 min | 0% |
| Bermuda Rd | 22.6 min | 22.4 min | 0% |
| I-15 S | 25.9 min | 26.1 min | 0% |

_Analysis window: 8:30–9:05am only (50 samples)._

- **Route:** S Spencer St (shortest road at 12.65 km, near-zero delay)
- **Leave home:** 8:39am → arrives ~9:00am
- **Worst recorded arrival:** 9:01am — the 9:10am hard limit is never at risk
- Travel time spread across all mornings: only **1.2 minutes** (19.6–20.8 min)

#### Afternoon pick-up

| Route | Avg Travel | Worst Ever | Ranked #1 |
|---|---|---|---|
| **S Maryland Pkwy** | **22.2 min** | **23.4 min** | **90%** |
| Bermuda Rd | 23.1 min | 23.7 min | 16% |
| S Spencer St | 23.4 min | 24.4 min | 22% |
| S Eastern Ave | 25.0 min | 26.3 min | 0% |
| I-15 S | 27.5 min | 27.8 min | 0% |

_Analysis window: 2:40–4:00pm only (171 samples)._

- **Route:** S Maryland Pkwy (fastest 90% of afternoons)
- **Leave home:** 3:03pm → arrives ~3:25pm
- **Worst recorded arrival:** 3:26pm
- **Don't leave after 3:05pm** — the 3:10–3:25pm departure window adds ~1 minute of traffic on average

#### Key insight

S Spencer St dominates the morning but is never competitive in the afternoon (it carries a **3.4 min traffic delay penalty** after 2:30pm). S Maryland Pkwy is rarely competitive in the morning. Sticking to one route both ways costs roughly **2 minutes per round trip every day**.

---

## File Structure

```
school-run-background-app/
├── school_run_collector.py     # Main collector script
├── com.schoolrun.collector.plist  # launchd service definition (template)
├── install.sh                  # One-command installer
├── .env.example                # Configuration template
├── .gitignore
├── csv/
│   └── school_run_data.csv     # Collected route data
└── README.md
```

---

## Google Maps Links

Pre-loaded routes for the winning roads:

| Journey | Link |
|---|---|
| Drop-off (S Spencer St) | [Open in Google Maps](https://www.google.com/maps/dir/1948+Tanner+Valley+Circle,+Las+Vegas,+NV+89123/S+Spencer+St,+Las+Vegas,+NV/3200+Artella+Ave,+Henderson,+NV+89044) |
| Pick-up (S Maryland Pkwy) | [Open in Google Maps](https://www.google.com/maps/dir/1948+Tanner+Valley+Circle,+Las+Vegas,+NV+89123/S+Maryland+Pkwy,+Las+Vegas,+NV/3200+Artella+Ave,+Henderson,+NV+89044) |

---

## License

MIT
