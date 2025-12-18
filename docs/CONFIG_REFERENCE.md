# VIRALOS PRIME v2.0 - Configuration Reference

## Environment Variables (.env)

### Required

```bash
# OpenRouter API (optional - has fallback)
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# YouTube API (optional - can queue for later)
YOUTUBE_CLIENT_ID=xxx.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=xxx
YOUTUBE_REFRESH_TOKEN=xxx
```

### Optional

```bash
# Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx

# Email alerts
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ALERT_EMAIL=alerts@yourdomain.com

# System
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
ENVIRONMENT=production  # development, staging, production
MAX_DAILY_VIDEOS=7
MAX_MEMORY_GB=4.5
```

## Configuration Files

### config/niche_multipliers.json

Controls earnings optimization by content niche.

```json
{
  "niches": {
    "niche_name": {
      "multiplier": 1.8,
      "keywords": ["keyword1", "keyword2"],
      "description": "Niche description"
    }
  },
  "default_multiplier": 1.0
}
```

**Parameters**:
- `multiplier` (float, 0.1-2.0): Earnings multiplier for niche
- `keywords` (array): Keywords to detect this niche
- `description` (string): Human-readable description

**Tuning**:
- Increase multiplier for high-performing niches
- Decrease for low-performing or saturated niches
- Review quarterly based on actual earnings data

### config/publishing_schedule.json

Controls video publishing times and cadence.

```json
{
  "shorts": {
    "daily_count": 6,
    "publish_times_utc": [
      {"hour": 13, "minute": 0, "reason": "Early afternoon ET peak"}
    ],
    "minimum_spacing_hours": 2,
    "max_per_day": 8
  },
  "longform": {
    "daily_count": 1,
    "publish_times_utc": [
      {"hour": 14, "minute": 0, "reason": "Peak afternoon ET"}
    ],
    "preferred_days": ["tuesday", "wednesday", "thursday"],
    "avoid_days": ["friday", "saturday", "sunday"],
    "max_per_day": 2
  }
}
```

**Parameters**:
- `daily_count` (int): Target videos per day
- `publish_times_utc` (array): Scheduled publish times
- `minimum_spacing_hours` (int): Min time between videos
- `preferred_days` (array): Best days for publishing
- `avoid_days` (array): Days to skip long-form

**Tuning**:
- Adjust times based on audience timezone
- Use learned rules from weekly analysis
- A/B test different schedules

### config/narrative_lanes.json

Defines content strategy lanes and quotas.

```json
{
  "lanes": {
    "lane_id": {
      "name": "Lane Name",
      "percentage_min": 25,
      "percentage_max": 30,
      "description": "What this lane covers",
      "keywords": ["keyword1", "keyword2"],
      "tone": "analytical, skeptical",
      "examples": ["Example 1", "Example 2"]
    }
  },
  "allocation_rules": {
    "enforce_quotas": true,
    "allow_flexibility": 0.05,
    "rebalance_weekly": true
  }
}
```

**Parameters**:
- `percentage_min/max` (int): Lane quota range
- `keywords` (array): Keywords to assign topics to lane
- `tone` (string): Expected content tone
- `enforce_quotas` (bool): Strict quota enforcement
- `allow_flexibility` (float): Flexibility percentage

**Tuning**:
- Adjust percentages based on audience engagement
- Add/remove lanes based on content performance
- Update keywords as trends evolve

### config/safety_rules.json

Content safety and governance rules.

```json
{
  "hard_blocklist": {
    "categories": [
      {
        "name": "category_name",
        "keywords": ["banned1", "banned2"],
        "patterns": ["description of banned content"]
      }
    ]
  },
  "soft_blacklist": {
    "categories": [
      {
        "name": "category_name",
        "keywords": ["sensitive1"],
        "required_attribution": true,
        "min_sources": 1
      }
    ]
  },
  "quarantine_rules": {
    "threshold_daily_violations": 3,
    "threshold_percentage": 0.1
  }
}
```

**Parameters**:
- `hard_blocklist`: Immediate rejection keywords
- `soft_blacklist`: Requires attribution/disclaimer
- `threshold_daily_violations` (int): Max violations before alert
- `threshold_percentage` (float): Max violation rate

**Tuning**:
- Add keywords based on violations
- Review quarantined content weekly
- Balance safety vs. content variety

### config/github_actions_limits.json

Resource allocation and cost controls.

```json
{
  "job_limits": {
    "max_job_duration_minutes": 360,
    "target_daily_production_minutes": 105,
    "max_concurrent_jobs": 20
  },
  "cost_targets": {
    "max_monthly_usd": 50.0,
    "max_daily_usd": 2.0,
    "alert_threshold_usd": 40.0
  },
  "parallelism": {
    "shorts_parallel": 6,
    "sense_sources_parallel": 8,
    "enabled": true
  }
}
```

**Parameters**:
- `max_job_duration_minutes` (int): GitHub Actions timeout
- `max_monthly_usd` (float): Monthly budget
- `shorts_parallel` (int): Parallel video production
- `enabled` (bool): Enable/disable parallelism

**Tuning**:
- Increase parallelism to speed up
- Decrease to reduce costs
- Monitor actual costs vs. targets

### config/schemas.json

JSON schemas for data validation (read-only, do not edit unless adding features).

## Validation Rules (Code)

### src/validation/validator.py

```python
self.base_rules = {
    "min_source_count": 2,
    "max_explainability_seconds": 60,
    "min_relevance": 0.5,
    "valid_emotions": ["surprise", "concern", "curiosity", "awe"],
}
```

**Tuning**:
- `min_source_count`: Lower to accept more topics (quality risk)
- `max_explainability_seconds`: Raise to allow complex topics
- `min_relevance`: Lower to broaden content scope
- Add emotions to `valid_emotions` for more variety

## Scoring Weights (Code)

### src/scoring/vps_scorer.py

```python
self.weights = {
    "emotional_charge": 0.15,
    "curiosity_gap": 0.20,
    "timeliness": 0.10,
    "shareability": 0.15,
    "simplicity": 0.10,
    "historical_pattern": 0.10,
    "narrative_continuity": 0.15,
}
```

**Tuning**:
- Sum must equal 1.0
- Increase `curiosity_gap` for clickability
- Increase `timeliness` for trending topics
- Increase `historical_pattern` to favor proven formats

## LLM Configuration (Code)

### src/generation/llm_client.py

```python
self.model = "anthropic/claude-3.5-sonnet"
self.timeout_primary = 10
self.timeout_fallback = 5
```

**Models Available** (OpenRouter):
- `anthropic/claude-3.5-sonnet` - Best quality, higher cost
- `anthropic/claude-3-haiku` - Fast, lower cost
- `openai/gpt-4-turbo` - Alternative high quality
- `openai/gpt-3.5-turbo` - Budget option

**Tuning**:
- Switch model based on budget
- Adjust timeouts based on model speed
- Monitor quality vs. cost tradeoff

## Rate Limits (Code)

### src/shared/token_bucket.py

```python
# OpenRouter rate limit
rate_limiter.consume(
    "openrouter",
    tokens=1,
    capacity=100,
    refill_rate=100,
    refill_period=3600  # 1 hour
)
```

**Tuning**:
- Adjust `capacity` based on API tier
- Adjust `refill_rate` to match your quota
- Add rate limiters for other APIs as needed

## Cache TTL Settings

### src/shared/cache_manager.py

```python
cache_manager.set("namespace", "key", value, ttl_hours=24)
```

**Default TTLs**:
- Trends: 24 hours
- Assets: 168 hours (7 days)
- Embeddings: Permanent (until cache full)

**Tuning**:
- Lower TTL to get fresher data (more API calls)
- Raise TTL to reduce API calls (staler data)
- Balance freshness vs. cost

## Memory Settings

### src/memory/rci_manager.py

```python
self.half_life_days = 90
self.max_age_days = 270
```

**Tuning**:
- `half_life_days`: How quickly old data decays
- `max_age_days`: When to delete data (3x half-life)
- Shorter = less storage, less historical data
- Longer = more learning data, more storage

## Production Settings

### src/production/video_assembler.py

```python
if aspect_ratio == "9:16":
    width, height = 1080, 1920
else:
    width, height = 1920, 1080
```

**Resolution Options**:
- 1080x1920 (9:16 Shorts): Default
- 720x1280 (9:16 Shorts): Lower quality, faster
- 1920x1080 (16:9 Long): Default
- 1280x720 (16:9 Long): Lower quality, faster

**FFmpeg Presets**:
- `ultrafast`: Current default, fast but larger files
- `fast`: Better compression, slower
- `medium`: Good balance for long-form

## Workflow Schedules

### .github/workflows/*.yml

```yaml
schedule:
  - cron: '0 10 * * *'  # 10 AM UTC daily
```

**Cron Format**: `minute hour day month weekday`

**Examples**:
- `0 10 * * *` - 10 AM UTC daily
- `0 */2 * * *` - Every 2 hours
- `0 10 * * 6` - 10 AM Saturday only
- `0 13,15,17 * * *` - 1 PM, 3 PM, 5 PM daily

**Tuning**:
- Adjust to match audience timezone
- Space out workflows to avoid conflicts
- Consider API rate limits and quotas

## Quick Optimization Guide

### To Increase Speed:
1. Raise `shorts_parallel` in github_actions_limits.json
2. Use faster LLM model
3. Lower video resolution
4. Reduce video duration in EDG

### To Reduce Costs:
1. Use template engine (set OPENROUTER_API_KEY="")
2. Lower `daily_count` in publishing_schedule.json
3. Increase cache TTL
4. Use cheaper LLM model

### To Improve Quality:
1. Raise validation `min_relevance`
2. Use better LLM model
3. Increase `min_source_count`
4. Adjust VPS weights for your goals

### To Increase Output:
1. Raise `daily_count` in publishing_schedule.json
2. Lower validation `min_relevance`
3. Add more trend sources
4. Relax validation rules
