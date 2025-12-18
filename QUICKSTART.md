# VIRALOS PRIME v2.0 - Quick Start Guide

## 5-Minute Setup

### 1. Clone & Install
```bash
git clone <repo>
cd <repo>
./setup.sh
```

### 2. Configure (Optional)
```bash
cp .env.example .env
# Edit .env - add API keys (optional, has fallbacks)
```

### 3. Test Locally
```bash
cd src
python main.py daily
```

Expected output: Daily production runs, creates videos (or placeholders if no FFmpeg)

## GitHub Actions Deployment

### 1. Set Secrets
Go to: https://github.com/Ytt1/8n7t2vh7/settings/secrets/actions

Add:
- `OPENROUTER_API_KEY` (optional)
- `YOUTUBE_CLIENT_ID` (optional)
- `YOUTUBE_CLIENT_SECRET` (optional)
- `YOUTUBE_REFRESH_TOKEN` (optional)

### 2. Enable Workflows
Go to: https://github.com/Ytt1/8n7t2vh7/actions

Enable all workflows:
- ✅ Daily Production
- ✅ Shorts Publisher
- ✅ Weekly Learning
- ✅ Recovery Worker
- ✅ Manual Trigger
- ✅ Health Check

### 3. Trigger First Run
- Go to: https://github.com/Ytt1/8n7t2vh7/actions/workflows/manual_trigger.yml
- Click "Run workflow"
- Select "daily"
- Click "Run workflow"
- Wait ~105 minutes
- Check artifacts for results

## Mobile Triggering

### GitHub App (Easiest)
1. Install GitHub app on phone
2. Open repository
3. Go to Actions tab
4. Select "Manual Trigger"
5. Tap "Run workflow"
6. Choose mode, tap "Run"

### Browser (Works on Any Phone)
1. Open: https://github.com/Ytt1/8n7t2vh7/actions/workflows/manual_trigger.yml
2. Tap "Run workflow" button
3. Select mode
4. Tap "Run workflow"

### Curl (Terminal)
```bash
# Get GitHub Personal Access Token:
# https://github.com/settings/tokens (needs workflow scope)

curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.github.com/repos/Ytt1/8n7t2vh7/actions/workflows/manual_trigger.yml/dispatches \
  -d '{"ref":"feat/viralos-prime-v2-autonomous-youtube-automation","inputs":{"mode":"daily"}}'
```

## Check System Status

### Via GitHub
- Actions tab: https://github.com/Ytt1/8n7t2vh7/actions
- Check recent runs
- Download artifacts to see metrics

### Via Local Files
```bash
# Daily summary
cat data/metrics/daily_summary.json

# Recent logs
tail -f data/logs/*.log | jq

# Queue status
ls -la data/queue/
```

## Common Commands

```bash
# Run daily production
cd src && python main.py daily

# Run weekly learning
cd src && python main.py weekly

# Run recovery (retry failed)
cd src && python main.py recovery

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Debug mode
LOG_LEVEL=DEBUG python main.py daily

# Check FFmpeg
ffmpeg -version

# Check Python dependencies
pip list
```

## Expected Behavior

### First Run
- Discovers 50-100 trends
- Validates to 15-30 candidates
- Scores and ranks
- Selects 7 topics (6 shorts + 1 long)
- Generates content (uses templates if no LLM)
- Produces videos (or placeholders if no FFmpeg)
- Queues for publishing (if no YouTube auth)

### Daily Runs
- 10 AM UTC: Daily production starts
- ~105 minutes: Completes
- Throughout day: Publishes at scheduled times
- Videos appear on YouTube (if configured)

### Weekly Runs
- Saturday 10 AM UTC: Learning analysis
- Generates learned rules
- Commits to repository
- Applied to next week's content

## Troubleshooting

### No videos created
- Check FFmpeg: `ffmpeg -version`
- Install: `sudo apt-get install ffmpeg`

### LLM errors
- System uses fallback templates automatically
- Check API key in .env (optional)

### Publishing fails
- Videos queued in `data/queue/`
- Recovery worker retries every 2 hours
- Configure YouTube OAuth when ready

### Out of memory
- Clear cache: `rm -rf data/cache/*`
- Prune old data: See TROUBLESHOOTING.md

### Tests fail
```bash
pip install -r requirements.txt
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

## What's Happening?

### Daily Production Pipeline
1. **SENSE**: Fetch trends from Reddit, HN, RSS
2. **VALIDATION**: Filter by quality (consensus, emotion, relevance)
3. **SCORING**: Rank by VPS score (niche multipliers, saturation)
4. **DECISION**: Select 6 shorts + 1 long across narrative lanes
5. **GENERATION**: Create hooks, EDG, metadata (LLM or templates)
6. **SAFETY**: Check blocklists, require attribution
7. **PRODUCTION**: Assemble videos with FFmpeg
8. **PUBLISHING**: Upload to YouTube at scheduled times
9. **MEMORY**: Store performance data for learning

### Weekly Learning
1. Load past 7 days of RCI records
2. Statistical analysis (t-tests, effect sizes)
3. Generate learned rules
4. Apply to future content

## Next Steps

1. ✅ **Local test**: Run `python main.py daily`
2. ✅ **GitHub secrets**: Add API keys
3. ✅ **Manual trigger**: Test from phone
4. ✅ **Monitor**: Check Actions tab
5. ✅ **Review docs**: See docs/ folder

## Resources

- **README.md** - Full documentation
- **docs/ARCHITECTURE.md** - How it works
- **docs/CONFIG_REFERENCE.md** - Tune settings
- **docs/TROUBLESHOOTING.md** - Fix issues
- **docs/RUNBOOK.md** - Operations guide

## Support

- Check logs: `data/logs/*.log`
- Check metrics: `data/metrics/`
- Review workflows: `.github/workflows/`
- Create GitHub issue with error details

---

**You're ready!** System is fully autonomous once configured.
