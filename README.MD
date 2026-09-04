# Anime Release CLI

[![Version](https://img.shields.io/badge/version-1.2.0-blue)](https://github.com/LeftfaceKing/anime-release-cli/releases/tag/v1.2.0)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![CLI](https://img.shields.io/badge/interface-CLI-lightgrey)](https://github.com/LeftfaceKing/anime-release-cli)
[![License](https://img.shields.io/badge/license-Portfolio%20%2F%20Educational-lightgrey)](https://github.com/LeftfaceKing/anime-release-cli)

A command-line application for searching anime, viewing seasonal releases, checking episode schedules, discovering streaming availability, and tracking what is airing yesterday, today, and tomorrow.

Built in Python with data from AniList, Kitsu, and Tsuzuki.

## Features

- Self-update directly from the terminal with `ani update`
- Search for anime from the terminal
- View detailed anime information
- Browse anime by season
- Find anime by studio
- View upcoming releases
- Check yesterday's, today's, and tomorrow's airing schedules
- View complete episode schedules for currently airing anime
- Display RAW, SUB, and DUB release information
- Display streaming platforms when available
- View anime relations such as sequels, prequels, and side stories
- Automatic API fallback when a provider is unavailable
- Local timezone conversion for episode release times
- Globally accessible `ani` command with pipx

## Data Architecture

Anime Release CLI uses multiple data providers rather than depending on a single API.

```text
                 Anime Release CLI
                         |
          +--------------+--------------+
          |              |              |
       AniList          Kitsu         Tsuzuki
          |              |              |
       Metadata        Fallback       Airing &
       Search          Metadata       Schedule Data
       Relations       Seasons        Platforms
```

### AniList

AniList is the primary source for anime metadata, search results, relations, studios, seasonal information, and airing information when available.

### Kitsu

Kitsu provides fallback metadata when AniList is unavailable.

This allows commands such as search, info, season, and upcoming to continue functioning during an AniList outage.

### Tsuzuki

Tsuzuki provides detailed schedule information including:

- Episode numbers
- RAW releases
- SUB releases
- DUB releases
- Streaming platforms
- Schedule corrections
- Estimated release times

This is used for the detailed `airing` command and as a schedule fallback when AniList is unavailable.

## Engineering Highlights

Anime Release CLI demonstrates more than basic API consumption. The project was designed around reliability, data normalization, and real-world command-line usability.

- **Multi-provider API architecture** — integrates AniList, Kitsu, and Tsuzuki rather than relying on a single external service.
- **Automatic API failover** — commands continue operating through fallback providers when the primary AniList API is unavailable.
- **Data normalization** — converts responses from GraphQL and REST APIs into a consistent internal structure.
- **Schedule aggregation** — processes RAW, SUB, and DUB release schedules along with streaming platform information.
- **Local timezone conversion** — converts release timestamps into the user's local system timezone.
- **Fault-tolerant networking** — handles API outages, HTTP errors, timeouts, rate limits, and malformed responses without exposing Python tracebacks to the user.
- **CLI packaging** — packaged as an installable Python application with a global `ani` command using pipx.
- **Versioned releases** — uses Git tags and GitHub Releases for stable software releases.

### Real-World Problem Solved

Anime release information is distributed across multiple services and can become unavailable when a provider experiences an outage. Anime Release CLI combines multiple data sources behind one command-line interface and automatically falls back to alternative providers when necessary.

This allows users to search anime, inspect seasonal releases, check airing schedules, and view streaming information without manually switching between multiple websites or APIs.

## Requirements

- Python 3.10+
- Internet connection
- pipx recommended for global installation

## Installation

Anime Release CLI is designed to be installed with pipx.

```bash

pipx install git+https://github.com/LeftfaceKing/anime-release-cli.git

Clone the repository:

```bash
git clone <repository-url>
cd anime-release-cli
```

Install globally with pipx:

```bash
pipx install .
```

After installation, the CLI can be used from any directory:

```bash
ani --help
```

Check the installed version:

```bash
ani --version
```

Current release:

```text
Anime Release CLI 1.2.0
```

## Commands

### Search

Search for an anime:

```bash
ani search "Attack on Titan"
```

When multiple entries are found, the CLI allows you to select the correct season, movie, OVA, or other entry.

### Anime Information

Display detailed information:

```bash
ani info "Attack on Titan"
```

Information can include:

```text
Status
Format
Episodes
Source
Studio
Genres
Season
Start date
End date
Next episode
Air date
Countdown
Description
```

### Episode Schedule

Check the next available episode schedule:

```bash
ani schedule "Attack on Titan"
```

### Detailed Airing Schedule

Display the complete available episode schedule for a currently airing anime:

```bash
ani airing "Ghost in the shell"
```

Example:

```text
THE GHOST IN THE SHELL
----------------------------------------------------------------------

Status:     RELEASING
Format:     TV
Episodes:   10
Source:     MANGA
Studio:     Science SARU
Genres:     Action, Psychological, Sci-Fi
Started:    07/07/2026

STREAMING
----------------------------------------------------------------------

  YouTube
  Amazon Prime Video

EPISODE SCHEDULE
----------------------------------------------------------------------

Episode 1
  RAW   Tue, Jul 07, 2026 at 09:00 AM CDT
  ~SUB  Tue, Jul 07, 2026 at 09:00 AM CDT | Amazon Prime Video

Schedule data: Tsuzuki
Metadata source: AniList
```

Times are automatically displayed using the computer's local timezone.

### Today

Show anime airing today:

```bash
ani today
```

Example:

```text
AIRING TODAY
----------------------------------------------------------------------

07:00 AM Episode 9 Clevatess Season 2 | RAW
07:00 AM Episode 9 Clevatess Season 2 | SUB | Crunchyroll
```

### Tomorrow

Show tomorrow's schedule:

```bash
ani tomorrow
```

### Yesterday

Show yesterday's schedule:

```bash
ani yesterday
```

### Seasonal Anime

Browse a season:

```bash
ani season fall-2026
```

Supported seasons:

```text
winter
spring
summer
fall
```

Example:

```bash
ani season summer-2026
```

Filter by studio when studio information is available:

```bash
ani season fall-2026 --studio "MAPPA"
```

### Upcoming Anime

View upcoming releases:

```bash
ani upcoming
```

### Studio Search

Find anime from a studio:

```bash
ani studio "MAPPA"
```

### Relations

View related anime:

```bash
ani relations "Attack on Titan"
```

Relations can include:

```text
PREQUEL
SEQUEL
SIDE STORY
SPIN OFF
ALTERNATIVE
SUMMARY
COMPILATION
SOURCE
ADAPTATION
```

## Automatic API Fallback

The CLI is designed to remain usable when one of its upstream providers experiences an outage.

For metadata operations:

```text
AniList
   |
   | unavailable
   v
Kitsu
```

For daily schedule operations:

```text
AniList
   |
   | unavailable
   v
Tsuzuki
```

For detailed airing schedules, Tsuzuki provides schedule data while AniList metadata is used where available.

This multi-provider architecture reduces the likelihood that an outage from a single service makes the entire CLI unusable.

## Command Reference

```text
ani search "Anime Name"
ani info "Anime Name"
ani schedule "Anime Name"
ani airing "Anime Name"
ani relations "Anime Name"
ani studio "Studio Name"
ani season fall-2026
ani season fall-2026 --studio "Studio Name"
ani upcoming
ani yesterday
ani today
ani tomorrow
ani --version
ani --help
```

## Project Structure

```text
anime-release-cli/
├── src/
│   ├── api.py
│   ├── formatters.py
│   ├── main.py
│   └── models.py
├── tests/
├── .gitignore
├── pyproject.toml
├── README.MD
└── requirements.txt
```

## Updating a Local pipx Installation

After modifying the source code, reinstall the application:

```bash
cd "/path/to/anime-release-cli"
pipx install --force .
```

Verify the installation:

```bash
ani --version
```

## Error Handling

The CLI handles common API and network problems without exposing Python tracebacks during normal operation.

Handled conditions include:

- API outages
- HTTP errors
- Connection failures
- Request timeouts
- Rate limits
- Invalid API responses
- Empty search results
- Provider fallback failures

## Version

**Anime Release CLI v1.2.0**

## Technology

- Python
- argparse
- requests
- REST APIs
- GraphQL
- AniList API
- Kitsu API
- Tsuzuki API
- pipx

## Purpose

Anime Release CLI was built as a practical command-line application for retrieving and organizing anime release information from multiple external APIs.

The project demonstrates API integration, GraphQL and REST consumption, provider fallback architecture, data normalization, error handling, local timezone processing, Python packaging, and CLI application development.

## License

This project is intended for educational and portfolio use.

Anime information belongs to its respective data providers and rights holders.