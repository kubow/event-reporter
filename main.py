import argparse
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
import requests

# iCal URLs from Mike Riversdale's Rugby Calendar
# https://www.mikeriversdale.co.nz/rugby-calendar
ICAL_FEEDS = {
    "international": "https://www.google.com/calendar/ical/ct240d39oc9kq21cq3bn70jii8%40group.calendar.google.com/public/basic.ics",
}


def get_channel_ids(db_path: str = "stations.sqlite.db") -> list[dict]:
    """Load channel IDs from SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM channels")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def fetch_epg(channel_id: str, date_str: str, verbose: bool = False) -> dict | None:
    """Fetch EPG data for a channel from epg.pw API."""
    url = f"https://epg.pw/api/epg.json?lang=en&date={date_str}&channel_id={channel_id}"
    if verbose:
        print(f"  → Fetching: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if verbose:
            program_count = len(data.get("epg_list", []))
            print(f"    ✓ Got {program_count} programs")
        return data
    except requests.RequestException as e:
        print(f"Error fetching EPG for channel {channel_id}: {e}")
        return None


def search_rugby_in_epg(epg_data: dict, channel_name: str = "") -> list[dict]:
    """Search for rugby programs in EPG data."""
    rugby_matches = []
    if not epg_data:
        return rugby_matches
    
    programs = epg_data.get("epg_list", [])
    
    for program in programs:
        title = program.get("title", "").lower()
        description = (program.get("desc") or "").lower()
        if "rugby" in title or "rugby" in description:
            rugby_matches.append({
                "channel": channel_name,
                "title": program.get("title", ""),
                "start": program.get("start_date", ""),
                "end": program.get("end_date", ""),
                "description": program.get("desc") or ""
            })
    return rugby_matches


def process_tv_sport(verbose: bool = False, days: int = 1):
    """Check all channels from database for rugby programs."""
    script_dir = Path(__file__).parent
    db_path = script_dir / "stations.sqlite.db"
    
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return
    
    channels = get_channel_ids(str(db_path))
    print(f"📺 Checking {len(channels)} channels for rugby ({days} days)...")
    
    if verbose:
        print(f"Database: {db_path}")
        print("Channels:")
        for ch in channels:
            print(f"  - {ch.get('name', 'Unknown')} (ID: {ch.get('channel_id')})")
        print()
    
    all_rugby_matches = []
    seen = set()  # Deduplicate by channel + title + start time
    
    for day_offset in range(days):
        check_date = date.today() + timedelta(days=day_offset)
        date_str = check_date.strftime("%Y%m%d")
        
        if verbose:
            print(f"\n📅 {check_date.strftime('%A, %B %d, %Y')}")
        
        for channel in channels:
            channel_id = channel.get("channel_id") or channel.get("id")
            channel_name = channel.get("name", f"Channel {channel_id}")
            
            if verbose:
                print(f"[{channel_name}]")
            
            epg_data = fetch_epg(channel_id, date_str, verbose=verbose)
            rugby_matches = search_rugby_in_epg(epg_data, channel_name)
            
            for match in rugby_matches:
                key = (match['channel'], match['title'], match['start'])
                if key not in seen:
                    seen.add(key)
                    all_rugby_matches.append(match)
    
    # Sort by start time and group by date
    all_rugby_matches.sort(key=lambda x: x['start'])
    
    if all_rugby_matches:
        print(f"\n🏉 Rugby on TV ({len(all_rugby_matches)} broadcasts):\n")
        current_date = None
        for match in all_rugby_matches:
            # Parse date from ISO format
            match_date = match['start'][:10] if match['start'] else ""
            if match_date != current_date:
                current_date = match_date
                print(f"📅 {current_date}")
            
            time_str = match['start'][11:16] if len(match['start']) > 16 else ""
            print(f"   🏉 {time_str} [{match['channel']}] {match['title']}")
    
    print(f"\n{'─' * 50}")
    if not all_rugby_matches:
        print("No rugby programs found.")
    else:
        print(f"✅ Total: {len(all_rugby_matches)} rugby broadcasts!")


def fetch_ical_events(url: str, verbose: bool = False) -> list[dict]:
    """Fetch and parse iCal feed."""
    try:
        from icalendar import Calendar
    except ImportError:
        print("icalendar not installed. Run: pip install icalendar")
        return []
    
    if verbose:
        print(f"  → Fetching: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        cal = Calendar.from_ical(response.content)
        
        events = []
        for component in cal.walk():
            if component.name == "VEVENT":
                dtstart = component.get('dtstart')
                dtend = component.get('dtend')
                events.append({
                    "title": str(component.get('summary', '')),
                    "start": dtstart.dt if dtstart else None,
                    "end": dtend.dt if dtend else None,
                    "location": str(component.get('location', '')),
                    "description": str(component.get('description', ''))[:200],
                })
        
        if verbose:
            print(f"    ✓ Got {len(events)} events")
        return events
    except Exception as e:
        print(f"Error fetching calendar: {e}")
        return []


def process_calendar_events(verbose: bool = False, days: int = 14):
    """Check rugby calendar feeds for upcoming events."""
    print(f"📆 Checking rugby calendars (next {days} days)...")
    
    today = datetime.now().date()
    end_date = today + timedelta(days=days)
    
    all_events = []
    
    for feed_name, url in ICAL_FEEDS.items():
        if verbose:
            print(f"\n[{feed_name.title()} Calendar]")
        
        events = fetch_ical_events(url, verbose=verbose)
        
        for event in events:
            start = event.get("start")
            if start is None:
                continue
            
            # Handle both date and datetime objects
            event_date = start.date() if hasattr(start, 'date') else start
            
            if today <= event_date <= end_date:
                event["feed"] = feed_name
                all_events.append(event)
    
    # Sort by date
    all_events.sort(key=lambda x: x.get("start") or datetime.max)
    
    if all_events:
        print(f"\n🏉 Upcoming Rugby Events ({len(all_events)}):\n")
        current_date = None
        for event in all_events:
            start = event.get("start")
            event_date = start.date() if hasattr(start, 'date') else start
            
            if event_date != current_date:
                current_date = event_date
                print(f"📅 {current_date.strftime('%A, %B %d, %Y')}")
            
            time_str = start.strftime('%H:%M') if hasattr(start, 'strftime') and hasattr(start, 'hour') else ""
            print(f"   🏉 {time_str} {event['title']}")
            if event.get("location"):
                print(f"      📍 {event['location']}")
    else:
        print("No upcoming rugby events found.")
    
    print(f"\n{'─' * 50}")
    print(f"✅ Total: {len(all_events)} events in next {days} days")


def process_rugbypass(verbose: bool = False, days: int = 7):
    """Check RugbyPass TV for streaming availability."""
    print(f"📺 Checking RugbyPass TV (next {days} days)...")
    print()
    print("⚠️  RugbyPass scraper not yet implemented.")
    print("   Will check: https://rugbypass.tv/home")
    print()
    print("Planned features:")
    print("  - Live match availability")
    print("  - Upcoming broadcasts")
    print("  - Region availability check")


def main():
    parser = argparse.ArgumentParser(
        description='Rugby event discovery across TV, calendars, and streaming.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py tv                  Check TV schedules for today
  python main.py tv --days 14        Check next 14 days
  python main.py events              Check calendar events
  python main.py rugbypass           Check streaming availability
        """
    )
    parser.add_argument('command', nargs='?', default='tv',
                        choices=['tv', 'events', 'rugbypass'],
                        help='What to check: tv, events, or rugbypass')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show detailed output')
    parser.add_argument('-d', '--days', type=int, default=1,
                        help='Number of days to check (default: 1)')
    
    args = parser.parse_args()
    
    if args.command == 'tv':
        process_tv_sport(verbose=args.verbose, days=args.days)
    elif args.command == 'events':
        process_calendar_events(verbose=args.verbose, days=args.days)
    elif args.command == 'rugbypass':
        process_rugbypass(verbose=args.verbose, days=args.days)


if __name__ == '__main__':
    main()
