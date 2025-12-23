# 🏉 Event Reporter

Automated rugby event discovery across TV schedules, public calendars, and streaming platforms.

## Features

| Workflow | Source | Description |
|----------|--------|-------------|
| `rugby_tv` | [epg.pw](https://epg.pw) | Scans TV channels (NOVA Sports, etc.) for rugby broadcasts |
| `rugby_events` | [Mike Riversdale Calendar](https://www.mikeriversdale.co.nz/rugby-calendar) | Parses public iCal feed for international fixtures |
| `rugby_pass` | [RugbyPass TV](https://rugbypass.tv) | Checks streaming availability *(planned)* |

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd event-reporter
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize database with channels
python init_db.py

# Run rugby TV checker
python main.py tv --verbose

# Run calendar events checker
python main.py events --verbose
```

## Commands

```bash
python main.py tv              # Check TV schedules for rugby
python main.py tv --verbose    # With detailed API output
python main.py events          # Check calendar events
python main.py events --days 14  # Look ahead 14 days
```

## Channel Database

Channels are stored in `stations.sqlite.db`. Add more channels:

```python
import sqlite3
conn = sqlite3.connect("stations.sqlite.db")
conn.execute("INSERT INTO channels (channel_id, name) VALUES (?, ?)", 
             ("12345", "Sky Sports Rugby"))
conn.commit()
```

Or edit `init_db.py` and re-run it.

### Finding Channel IDs

- [epg.pw Channel List](https://epg.pw/index.html?lang=en) - Search for channels, ID is in the URL
- [EPG IPTVX](https://epg.iptvx.one/) - Alternative source
- [Radio Times](https://www.radiotimes.com/tv/tv-listings/) - UK listings

## GitHub Actions

All workflows run **Monday morning** and create GitHub Issues with results:

| Workflow | Time (UTC) | Issue Label | Description |
|----------|------------|-------------|-------------|
| `rugby_tv.yml` | Mon 5 AM | `rugby-tv` | TV schedules for the week |
| `rugby_events.yml` | Mon 6 AM | `rugby-events` | Calendar fixtures for the week |
| `rugby_pass.yml` | Mon 7 AM | `weekly-digest` | Combined digest + streaming links |

### How Issues Work
- Creates a new issue each Monday with the week's rugby content
- Previous week's digest is auto-closed
- No issue created if no rugby found
- Labels: `automated`, `weekly-digest`, `rugby-tv`, `rugby-events`

## Data Sources

| Source | Type | Coverage |
|--------|------|----------|
| epg.pw API | JSON/XML | Global TV schedules |
| Mike Riversdale iCal | ICS | Men's & Women's international fixtures |
| RugbyPass | Web scraping | Streaming availability |

## Roadmap

- [ ] Extend channel list (full epg.pw catalog)
- [ ] Multiple search terms (rugby, NFL, documentaries)
- [ ] RugbyPass streaming checker
- [ ] Discord/Slack notifications
- [ ] Export to personal calendar

## Library Maintenance

```bash
python -m venv venv
source venv/bin/activate
pip-compile --upgrade --strip-extras requirements.in
pip install -r requirements.txt
```

## License

See [LICENSE](LICENSE)
