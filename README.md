# VIRALOS PRIME v2.0

**Fully Autonomous YouTube Automation System**

[![Daily Production](https://github.com/Ytt1/8n7t2vh7/actions/workflows/daily_production.yml/badge.svg)](https://github.com/Ytt1/8n7t2vh7/actions/workflows/daily_production.yml)

## Overview

VIRALOS PRIME v2.0 is a production-ready, fully autonomous YouTube automation system that:

- 🎯 **Produces 5-8 Shorts + 1 Long-form daily** with zero human involvement
- 📊 **Discovers trending topics** from multiple sources (Reddit, HackerNews, RSS feeds)
- 🤖 **Generates content** using LLM (OpenRouter) with fallback templates
- 🎬 **Assembles videos** using FFmpeg with automated EDG (Edit Decision Graph)
- 📤 **Publishes to YouTube** at optimal high-traffic times
- 📈 **Learns weekly** from performance data to improve over time
- 📱 **Triggerable from mobile** via GitHub Actions UI or curl commands

## Quick Start

### Prerequisites

- Python 3.9+
- FFmpeg installed
- OpenRouter API key (optional, has fallback)
- YouTube OAuth credentials (optional, can queue for later)

### Local Development

```bash
# Clone and install
git clone <repo>
cd <repo>
pip install -r requirements.txt

# Run daily production
cd src
python main.py daily

# Run weekly learning
python main.py weekly

# Run recovery worker
python main.py recovery
```

### GitHub Actions Deployment

1. **Set up secrets** in GitHub repository settings:
   - `OPENROUTER_API_KEY` - OpenRouter API key
   - `YOUTUBE_CLIENT_ID` - YouTube OAuth client ID
   - `YOUTUBE_CLIENT_SECRET` - YouTube OAuth client secret
   - `YOUTUBE_REFRESH_TOKEN` - YouTube OAuth refresh token

2. **Enable workflows** in Actions tab

3. **Trigger manually** or wait for scheduled runs

## Mobile Triggering

### Option 1: GitHub Mobile App (Easiest)

1. Open GitHub app
2. Navigate to repository → Actions tab
3. Select "Manual Trigger (Mobile Friendly)"
4. Click "Run workflow"
5. Select mode (daily/weekly/recovery)
6. Click "Run workflow" button

### Option 2: GitHub Web UI

1. Open https://github.com/Ytt1/8n7t2vh7/actions/workflows/manual_trigger.yml
2. Click "Run workflow" dropdown
3. Select mode and click "Run workflow"

### Option 3: Curl Command (Terminal)

```bash
# Get your GitHub Personal Access Token first from:
# https://github.com/settings/tokens

curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/Ytt1/8n7t2vh7/actions/workflows/manual_trigger.yml/dispatches \
  -d '{"ref":"feat/viralos-prime-v2-autonomous-youtube-automation","inputs":{"mode":"daily"}}'
```

## System Architecture

```
┌─────────────┐
│   SENSE     │  Discover trends from Reddit, HackerNews, RSS
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ VALIDATION  │  Filter by quality, relevance, emotion
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   SCORING   │  VPS v2.0 scoring with niche multipliers
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  DECISION   │  Select 6 shorts + 1 long via narrative lanes
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ GENERATION  │  Create hooks, EDG, metadata (LLM + templates)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ PRODUCTION  │  Assemble videos with FFmpeg
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ PUBLISHING  │  Upload to YouTube at optimal times
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   MEMORY    │  Store RCI records for learning
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  LEARNING   │  Analyze weekly, generate rules
└─────────────┘
```

## Key Features

### 🎯 Autonomous Operation

- **Daily Production**: Runs at 10 AM UTC, completes in ~105 minutes
- **Scheduled Publishing**: 6 shorts at 13:00, 15:00, 17:00, 21:00, 23:00, 02:00 UTC
- **Weekly Learning**: Saturday 10 AM, analyzes past 7 days
- **Recovery Worker**: Every 2 hours, retries failed publishes

### 📊 Multi-Source Trend Discovery

- Reddit (r/technology, r/business, r/finance, etc.)
- HackerNews top stories
- RSS feeds (BBC, Reuters)
- Semantic deduplication using embeddings
- Consensus requirement (2+ sources)

### 🧠 Intelligent Scoring

**VPS v2.0 Components** (0-100):
- Emotional charge (0.15)
- Curiosity gap (0.20)
- Timeliness (0.10)
- Shareability (0.15)
- Simplicity (0.10)
- Historical pattern (0.10)
- Narrative continuity (0.15)

**Niche Multipliers**:
- Finance: 1.8x
- AI/Tech: 1.6x
- Business: 1.4x
- Self-Improvement: 1.2x
- Crypto: 1.3x

**Final Score** = Base VPS × Niche Multiplier × Saturation Factor

### 🎬 Video Production

- **EDG (Edit Decision Graph)**: JSON-based deterministic video specs
- **FFmpeg Pipeline**: Automated assembly with text overlays
- **Fallback Chains**: 
  - LLM → Template engine
  - Stock assets → Cached assets → Abstract motion
  - TTS → Captions-only
- **Aspect Ratios**: 9:16 (Shorts), 16:9 (Long-form)

### 📈 Weekly Learning

- Analyzes past 7 days of RCI (Record, Context, Impact) data
- Statistical tests: T-tests, Mann-Whitney U, effect sizes
- Rule promotion: N≥10, effect_size≥0.5, p<0.05
- Auto-updates thumbnail styles, publishing times, hooks

### 🛡️ Safety & Governance

- **Hard blocklist**: Political endorsements, unverified accusations, medical/financial advice
- **Soft blacklist**: Requires attribution for controversial claims
- **Pre-publish scanning**: Titles, descriptions, scripts
- **Quarantine**: >10% violations triggers alert

## Performance Targets

- **Wall-clock time**: 105 minutes for daily production
- **Cost**: <$1/day GitHub Actions (<$50/month)
- **Memory**: <4.5 GB steady-state
- **Storage**: ~1 GB cache, ~0.5 GB RCI
- **API calls**: 7 OpenRouter/day, 7 YouTube/day

## Configuration

See `config/` directory for:

- `niche_multipliers.json` - Earnings optimization by niche
- `publishing_schedule.json` - Optimal publish times
- `narrative_lanes.json` - Content strategy lanes
- `safety_rules.json` - Hard/soft blocklists
- `github_actions_limits.json` - Resource constraints

## Monitoring

- **Metrics**: `data/metrics/daily_summary.json`
- **Logs**: `data/logs/` (structured JSON)
- **Queue**: `data/queue/` (failed publishes)
- **Memory**: `memory/rci_archive_YYYYMMDD.json`

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design and data flow
- [CONFIG_REFERENCE.md](docs/CONFIG_REFERENCE.md) - All configuration options
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Common issues and fixes
- [RUNBOOK.md](docs/RUNBOOK.md) - Incident response procedures

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest -m unit
pytest -m integration
```

## License

Proprietary - All Rights Reserved

## Status

✅ **Production Ready** - Fully autonomous, tested, and deployed

---

**VIRALOS PRIME v2.0** - Zero Daily Human Involvement
