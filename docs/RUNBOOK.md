# VIRALOS PRIME v2.0 - Operations Runbook

## Daily Operations

### Morning Check (10:00 AM UTC)
Daily production should start automatically.

**Actions**:
1. Verify workflow started: https://github.com/Ytt1/8n7t2vh7/actions
2. Check no errors in first 15 minutes
3. Monitor until completion (~105 minutes)

### Evening Verification (18:00 UTC)
Daily production should be complete.

**Actions**:
1. Check workflow completed successfully
2. Verify videos published: Check YouTube channel
3. Review metrics: `data/metrics/daily_summary.json`
4. Check queue is empty: `ls data/queue/`

## Weekly Operations

### Saturday Morning (10:00 AM UTC)
Weekly learning runs automatically.

**Actions**:
1. Verify workflow completes successfully
2. Review learned rules: `memory/learned_rules/learned_rules_*.json`
3. Check if any rules need manual review
4. Verify rules committed to repository

### Weekly Review (Saturday Afternoon)
Analyze system performance.

**Metrics to Check**:
- Total videos published this week
- Average VPS scores
- Pass rates (validation, safety)
- Queue length trends
- Memory usage trends
- Cost tracking

```bash
# Weekly metrics script
python << 'EOF'
import json
from pathlib import Path
from datetime import datetime, timedelta

cutoff = datetime.utcnow() - timedelta(days=7)
metrics_dir = Path("data/metrics")

summary_files = list(metrics_dir.glob("daily_summary.json"))
total_videos = 0

for f in summary_files:
    try:
        with open(f) as file:
            data = json.load(file)
            total_videos += data.get("videos_published", 0)
    except:
        pass

print(f"Videos this week: {total_videos}")
print(f"Average per day: {total_videos / 7:.1f}")
EOF
```

## Monthly Operations

### First of Month
System maintenance tasks.

**Actions**:
1. **Memory Compaction**:
   ```bash
   python scripts/compact_memory.py
   ```

2. **Cost Review**:
   - Check GitHub Actions usage
   - Review OpenRouter API costs
   - Verify staying under $50/month budget

3. **Niche Performance Review**:
   - Analyze which niches perform best
   - Update `config/niche_multipliers.json` if needed

4. **Safety Rule Review**:
   - Review quarantine logs
   - Update `config/safety_rules.json` if patterns emerge

## Incident Response

### Incident: Daily Production Failed

**Severity**: HIGH

**Detection**:
- Workflow status shows failed
- No videos published today
- Alert in GitHub Actions

**Response**:
1. Check workflow logs for error
2. Identify failing stage
3. Common fixes:
   - Restart workflow manually
   - Clear cache if memory issue
   - Use recovery worker for publishing failures
4. Document issue and resolution

**Recovery**:
```bash
# Manual production run
gh workflow run manual_trigger.yml -f mode=daily
```

### Incident: YouTube Quota Exceeded

**Severity**: MEDIUM

**Detection**:
- Publishing errors with "quotaExceeded"
- Videos queued but not published

**Response**:
1. Verify quota status in Google Cloud Console
2. Calculate videos in queue
3. Wait for quota reset (24 hours)
4. Do NOT reduce today's production (queue will handle)

**Recovery**:
- Recovery worker will automatically retry after quota reset
- Monitor queue: `ls data/queue/ | wc -l`

### Incident: LLM API Completely Down

**Severity**: LOW

**Detection**:
- All "LLM generation failed" logs
- Using fallback templates

**Response**:
1. No immediate action needed (fallback works)
2. Check OpenRouter status page
3. Monitor content quality

**Recovery**:
- System automatically recovers when API returns
- No manual intervention needed

### Incident: Memory Exceeds 4.5 GB

**Severity**: MEDIUM

**Detection**:
- "Memory limit exceeded" warnings
- Workflow slowdown

**Response**:
1. Immediate cleanup:
   ```bash
   rm -rf data/cache/*
   python -c "from src.memory import RCIManager; RCIManager().prune_old_records()"
   ```

2. Verify cleanup worked:
   ```bash
   du -sh data/cache data/assets memory
   ```

**Prevention**:
- Increase auto-cleanup frequency
- Lower cache TTL
- Reduce asset retention

### Incident: No Trends Discovered

**Severity**: MEDIUM

**Detection**:
- "Low trend count, adding evergreen" warning
- All sources failing

**Response**:
1. Check network connectivity
2. Test each source individually:
   ```bash
   python -c "from src.sense import TrendAggregator; a = TrendAggregator(); print(a._fetch_reddit())"
   ```
3. Verify source URLs haven't changed
4. Check for rate limiting

**Recovery**:
- System uses evergreen topics automatically
- Fix sources for next run
- Update source URLs if needed

### Incident: High Safety Violation Rate

**Severity**: HIGH

**Detection**:
- "Quarantine alert: >10% of daily content"
- Many videos suppressed

**Response**:
1. Review quarantined content: `ls data/quarantine_artifacts/`
2. Identify pattern (specific source? topic type?)
3. Update safety rules immediately
4. Restart production if needed

**Recovery**:
1. Edit `config/safety_rules.json`
2. Add offending patterns to blocklist
3. Re-run validation on today's content
4. Manual review before next run

## Maintenance Windows

### Planned Maintenance
Schedule during low-traffic periods (3-5 AM UTC).

**Notification**:
1. Create GitHub issue announcing maintenance
2. Disable scheduled workflows temporarily
3. Perform maintenance tasks
4. Re-enable workflows
5. Verify next run completes successfully

**Tasks**:
- System upgrades
- Dependency updates
- Configuration changes
- Database migrations (if added)

### Emergency Maintenance
For critical issues requiring immediate intervention.

**Process**:
1. Disable all workflows: Settings → Actions → Disable
2. Fix issue in code
3. Test locally: `python src/main.py daily`
4. Push fix to repository
5. Re-enable workflows
6. Monitor next scheduled run

## Monitoring

### Key Metrics

Monitor these daily:

| Metric | Target | Alert If |
|--------|--------|----------|
| Videos published | 7/day | <5/day |
| Validation pass rate | >50% | <40% |
| Safety violation rate | <5% | >10% |
| Queue length | 0-5 | >100 |
| Memory usage | <3 GB | >4.5 GB |
| Workflow duration | <105 min | >120 min |
| Cost | <$2/day | >$3/day |

### Alerting

**GitHub Actions Native**:
- Workflow failure → Email notification
- Job timeout → Automatic cancel + notification

**Custom Alerts** (optional):
- Set up Slack webhook in secrets
- Configure email SMTP in secrets
- Health check workflow creates GitHub issues

## Backup & Recovery

### Data Backup

**What to backup**:
- `memory/` - RCI archives and learned rules
- `config/` - All configuration files
- `data/metrics/` - Performance data

**Backup Schedule**:
```bash
# Weekly backup script (run on Sunday)
tar -czf backup_$(date +%Y%m%d).tar.gz memory/ config/ data/metrics/
```

**Restoration**:
```bash
# Extract backup
tar -xzf backup_YYYYMMDD.tar.gz
```

### Disaster Recovery

**Scenario**: Repository deleted or corrupted

**Recovery Steps**:
1. Clone from backup or GitHub
2. Restore secrets in repo settings
3. Verify all workflows present
4. Run health check: `gh workflow run health_check.yml`
5. Manual trigger test run: `gh workflow run manual_trigger.yml -f mode=recovery`
6. Resume scheduled operations

**RTO** (Recovery Time Objective): 2 hours
**RPO** (Recovery Point Objective): 24 hours (daily backups)

## Escalation

### Level 1: Automated Recovery
- Token bucket rate limiting
- Fallback template engine
- Queue retry system
- Cache fallback chain

### Level 2: Alert + Auto-Fix
- Memory cleanup triggers
- Safety rule relaxation
- Recovery worker retries

### Level 3: Manual Intervention
- Configuration changes needed
- API credential issues
- Source URL updates
- Safety rule updates

### Level 4: Code Changes Required
- Bug fixes
- Feature modifications
- Performance optimization
- New source integration

## Contacts

- **Repository Owner**: Ytt1
- **Repository**: https://github.com/Ytt1/8n7t2vh7
- **Branch**: feat/viralos-prime-v2-autonomous-youtube-automation

## On-Call Playbook

### High Priority Issues (respond within 1 hour)
- Daily production completely failed
- YouTube quota exceeded with full queue
- Safety violations >20%
- Memory leak causing crashes

### Medium Priority Issues (respond within 4 hours)
- Single workflow failure
- LLM API down (fallback working)
- Elevated queue length
- Performance degradation

### Low Priority Issues (respond within 24 hours)
- Single video failure
- Low trend discovery
- Minor safety violations
- Optimization opportunities

## Change Management

### Making Configuration Changes

1. **Test locally first**:
   ```bash
   python src/main.py daily
   ```

2. **Document change** in commit message

3. **Deploy during low-traffic period**

4. **Monitor next run** for issues

5. **Rollback if needed**:
   ```bash
   git revert HEAD
   git push
   ```

### Making Code Changes

1. **Create feature branch**
2. **Test thoroughly**:
   ```bash
   pytest
   python src/main.py daily
   ```
3. **Code review** (if team)
4. **Merge to main**
5. **Monitor production**

## Performance Tuning

### If workflow too slow:
1. Increase parallelism in config
2. Reduce video count
3. Optimize asset fetching
4. Use simpler EDG templates

### If costs too high:
1. Reduce LLM API calls (use templates more)
2. Lower video count
3. Optimize caching
4. Reduce artifact retention

### If quality degrading:
1. Review learned rules (may need demotion)
2. Adjust VPS weights
3. Increase validation strictness
4. Update niche multipliers
