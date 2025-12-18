# VIRALOS PRIME v2.0 - System Architecture

## Overview

VIRALOS PRIME v2.0 is built on a layered pipeline architecture with autonomous decision-making and continuous learning.

## System Layers

### 1. SENSE Layer
**Purpose**: Discover trending topics from multiple sources

**Sources**:
- Reddit (hot posts from targeted subreddits)
- HackerNews (top stories)
- RSS feeds (BBC, Reuters)

**Process**:
1. Fetch from all sources in parallel
2. Apply exponential backoff retry (3 attempts, 1s→5s)
3. Cache results (24h TTL)
4. Fallback chain: Live → 24h cache → 12h cache → Evergreen topics

**Output**: `trend_records.json` (50-100 candidates)

### 2. VALIDATION Layer
**Purpose**: Filter topics by quality and relevance

**Checks**:
- Source count ≥ 2 (consensus requirement)
- Explainability ≤ 60s (complexity filter)
- Emotional vector ∈ {surprise, concern, curiosity, awe}
- Relevance ≥ 0.5 (high-value niche keywords)

**Adaptive Behavior**:
- If pass rate < 50%, progressively relax constraints
- Track daily acceptance rate, alert if < 40%

**Output**: `validated_candidates.json` (15-30 topics)

### 3. SCORING Layer (VPS v2.0)
**Purpose**: Rank topics by earnings potential

**Formula**:
```
Final Score = Base VPS × Niche Multiplier × Saturation Factor
```

**Base VPS Components** (0-100):
- Emotional charge: 15%
- Curiosity gap: 20%
- Timeliness: 10%
- Shareability: 15%
- Simplicity: 10%
- Historical pattern: 10%
- Narrative continuity: 15%

**Niche Multipliers**:
- Finance: 1.8x
- AI/Tech: 1.6x
- Business: 1.4x
- Self-Improvement: 1.2x
- Crypto: 1.3x
- General: 1.0x

**Saturation Factor** (based on competitor count):
- 0-2 competitors: 1.8x boost
- 3-5 competitors: 1.0x neutral
- 6-15 competitors: 0.7x penalty
- 16-50 competitors: 0.3x penalty
- 50+ competitors: Skip topic

**Output**: `scored_candidates.json` (sorted by final score)

### 4. DECISION Layer
**Purpose**: Select daily content mix across narrative lanes

**Narrative Lanes**:
1. **AI & Power** (30-35%): AI systems, automation impact, tech power
2. **Market Inflection** (25-30%): Financial markets, economic shifts
3. **Hidden Data** (20-25%): Overlooked statistics, patterns
4. **Competitive Edge** (15-20%): Skills, strategies, advantages
5. **Contrarian Take** (10-15%): Challenge conventional wisdom

**Selection Process**:
1. Filter candidates with final score ≥ 70
2. Assign narrative lane based on keywords and niche
3. Enforce lane quotas with 5% flexibility
4. Select 6 Shorts + 1 Long-form
5. Ensure narrative diversity (max 2 consecutive same lane)

**Output**: `selection_plan.json` (7 videos with lane assignments)

### 5. GENERATION Layer
**Purpose**: Create hooks, scripts, EDG, and metadata

**LLM Integration**:
- Primary: OpenRouter API (Claude 3.5 Sonnet)
- Token bucket: 100k/hour
- Timeout: 10s primary, 5s fallback
- Retry: 3 attempts with exponential backoff

**Fallback**: Deterministic template engine (always works)

**Outputs per video**:
- **Hooks**: 3+ attention-grabbing phrases (8-12 words)
- **EDG**: Complete Edit Decision Graph (JSON)
- **Script**: ≤90 words (Short) / outline (Long)
- **Metadata**: Titles (2 variants), description, tags

**Persona Enforcement**:
- Cold, analytical, sourced skepticism
- No sensationalism without evidence
- Data-driven, neutral tone

### 6. PRODUCTION Layer
**Purpose**: Assemble videos from EDG

**EDG Schema**:
```json
{
  "video_id": "vid_abc123",
  "format": "short",
  "duration_seconds": 28,
  "aspect_ratio": "9:16",
  "scenes": [
    {
      "id": "scene_1",
      "type": "intro",
      "start": 0.0,
      "end": 3.0,
      "visual": "abstract_motion",
      "text_overlay": "Hook text",
      "tts_text": "Spoken text",
      "cut_type": "hard"
    }
  ]
}
```

**FFmpeg Pipeline**:
1. Parse EDG JSON
2. Fetch assets (stock video/images)
3. Build filtergraph (text overlays, pan/zoom, subtitles)
4. Render video (libx264, preset: ultrafast)
5. Verify output exists

**Fallback Chains**:
- Asset fetching: Try 3 queries → Cached → Abstract motion
- TTS: Kokoro → Piper → eSpeak → Captions-only
- Filter failure: Static images + cuts

**Output**: MP4 files (9:16 for Shorts, 16:9 for Long)

### 7. PUBLISHING Layer
**Purpose**: Upload videos to YouTube at optimal times

**YouTube API**:
- OAuth2 with auto-refresh (1 day before expiry)
- Resumable upload API (handles partial uploads)
- Quota checking (don't publish if <2 uploads remaining)

**Publish Modes**:
- **Canary**: Unlisted for 2h observation
- **Public**: Promoted if top 20% performance
- **Private**: Suppressed if bottom 50% performance

**Queue Management**:
- Failed publishes → `data/queue/`
- Recovery worker retries hourly
- Never lose videos due to auth failure

**Scheduling**:
- Shorts: 13:00, 15:00, 17:00, 21:00, 23:00, 02:00 UTC
- Long-form: 14:00 UTC (peak afternoon ET)
- Niche-specific optimization (Finance: 8-10 AM ET)

### 8. MEMORY Layer (RCI)
**Purpose**: Store performance data for learning

**RCI Record Schema**:
```json
{
  "video_id": "vid_abc123",
  "hook": "Here's what the data shows",
  "title": "AI Job Market Shift",
  "format": "short",
  "posting_time": "2024-01-15T14:00:00Z",
  "publishing_hour": 14,
  "day_of_week": "Monday",
  "early_signals": {
    "views_2h": 1200,
    "views_24h": 8500,
    "view_velocity": 354.2,
    "like_ratio": 0.042,
    "retention_percentile": 0.72
  },
  "niche": "ai_tech",
  "narrative_lane": "ai_power",
  "vps_score": 82.5
}
```

**Storage**:
- Append-only: `memory/rci_archive_YYYYMMDD.json`
- Exponential decay: Half-life 90 days
- Auto-prune: Delete >270 days
- Monthly compaction

### 9. LEARNING Layer
**Purpose**: Analyze performance and generate rules

**Weekly Analysis** (Saturday 10 AM):
1. Load past 7 days of RCI records
2. Statistical tests:
   - CTR by thumbnail_style
   - Retention by hook_type
   - View velocity by posting_hour
   - T-tests / Mann-Whitney U
3. Rule promotion criteria:
   - N ≥ 10 samples
   - Effect size ≥ 0.5 (Cohen's d)
   - p-value < 0.05
   - 95% CI doesn't cross zero

**Rule Types**:
- Thumbnail: Prefer high-contrast, emotion signaling
- Timing: Optimal publish hours by niche
- Hook: Opening phrases that drive clicks
- Format: Short vs Long performance by topic
- Narrative: Lane effectiveness by niche

**Learned Rule Schema**:
```json
{
  "rule_id": "thumbnail_20240115",
  "rule_type": "thumbnail",
  "condition": "thumbnail_style == 'high_contrast'",
  "action": "prefer high_contrast style",
  "effect_size": 0.62,
  "confidence": 0.85,
  "p_value": 0.03,
  "sample_size": 24,
  "status": "active"
}
```

### 10. GOVERNOR Layer
**Purpose**: Safety and compliance

**Hard Blocklist** (immediate rejection):
- Political endorsements
- Unverified accusations
- Medical/financial advice
- Conspiracy theories

**Soft Blacklist** (requires attribution):
- Controversial claims → Add source
- Sensitive topics → Respectful tone
- Financial implications → Disclaimer

**Pre-Publish Scan**:
- Title, description, script, captions
- Violation handling:
  - Hard → Suppress
  - Soft → Add attribution
  - Multiple soft → Quarantine

**Quarantine Alert**: >10% daily violations → Manual review

## Data Flow

```
Sense → Validation → Scoring → Decision → Generation → Production → Publishing
                                                                          ↓
                                                                      Memory
                                                                          ↓
                                                                      Learning
                                                                          ↓
                                                                    Adaptation
```

## GitHub Actions Orchestration

### Daily Production Workflow
- **Trigger**: 10 AM UTC daily + manual
- **Duration**: ~105 minutes
- **Parallelism**: 6 shorts assembled in parallel
- **Caching**: FFmpeg (100 MB), embeddings (300 MB), assets (50 MB)

### Shorts Publisher Workflow
- **Trigger**: 6 times daily at optimal hours
- **Duration**: ~5 minutes
- **Action**: Process queue, publish scheduled videos

### Weekly Learning Workflow
- **Trigger**: Saturday 10 AM UTC
- **Duration**: ~20 minutes
- **Action**: Analyze RCI, generate rules, commit to repo

### Recovery Worker Workflow
- **Trigger**: Every 2 hours
- **Duration**: ~10 minutes
- **Action**: Retry failed publishes, clear queue

### Health Check Workflow
- **Trigger**: Every 6 hours
- **Duration**: ~5 minutes
- **Action**: Monitor system health, alert on issues

## Resource Allocation

| Layer | Timeout | Max Memory |
|-------|---------|------------|
| Sense | 15 min | 1.0 GB |
| Validation | 10 min | 0.5 GB |
| Scoring | 10 min | 1.0 GB |
| Generation | 20 min | 1.5 GB |
| Production | 40 min | 2.0 GB |
| Publishing | 20 min | 0.5 GB |

**Total**: 105 minutes, 4.5 GB peak

## Failure Modes & Mitigation

| Failure | Mitigation |
|---------|------------|
| LLM API down | Template engine fallback |
| Asset fetch fails | Cached assets → Abstract motion |
| FFmpeg error | Degraded video (static + cuts) |
| YouTube quota exceeded | Queue for retry |
| OAuth expired | Auto-refresh + manual script |
| Network timeout | Exponential backoff (3 retries) |
| Memory exceeded | Cleanup cache + prune old data |

## Cost Optimization

- **GitHub Actions**: Free tier covers ~2000 minutes/month
- **OpenRouter**: 7 calls/day × $0.003/call = $0.63/month
- **YouTube API**: Free (10,000 quota/day)
- **Storage**: <10 GB (within free tier)

**Total**: <$1/month (target: <$50/month with headroom)
