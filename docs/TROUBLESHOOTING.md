# VIRALOS PRIME v2.0 - Troubleshooting Guide

## Common Issues

### 1. Daily Production Not Running

**Symptoms**: No new videos, no GitHub Actions runs

**Diagnosis**:
```bash
# Check workflow status
gh workflow view daily_production.yml

# Check recent runs
gh run list --workflow=daily_production.yml
```

**Solutions**:
- Verify GitHub Actions are enabled in repo settings
- Check if workflow file has syntax errors
- Manually trigger: `gh workflow run daily_production.yml`
- Verify secrets are set correctly

### 2. OpenRouter API Errors

**Symptoms**: "LLM generation failed" in logs, using fallback templates

**Diagnosis**:
```bash
# Check if API key is set
echo $OPENROUTER_API_KEY

# Test API key
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

**Solutions**:
- Verify API key is valid and has credits
- Check rate limits (100k tokens/hour)
- System will use fallback templates automatically
- No action needed if fallback is working

### 3. FFmpeg Not Found

**Symptoms**: "FFmpeg not available" error, placeholder videos created

**Diagnosis**:
```bash
# Check FFmpeg installation
ffmpeg -version

# Check in GitHub Actions
gh run view --log | grep ffmpeg
```

**Solutions**:
```bash
# Local: Install FFmpeg
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg          # macOS

# GitHub Actions: Already installed in workflow
# Verify workflow has: sudo apt-get install -y ffmpeg
```

### 4. YouTube Publishing Fails

**Symptoms**: Videos queued in `data/queue/`, not appearing on YouTube

**Diagnosis**:
```bash
# Check queue
ls -la data/queue/

# Check publish records
cat data/metrics/publish_*.json

# Check logs
grep "Publishing" data/logs/*.log
```

**Solutions**:
1. **OAuth Token Expired**:
   ```bash
   # Refresh token manually
   python scripts/refresh_youtube_token.py
   ```

2. **Quota Exceeded**:
   - Wait 24 hours for quota reset
   - Reduce daily video count in config

3. **Invalid Credentials**:
   - Verify secrets in GitHub: Settings → Secrets → Actions
   - Re-generate YouTube OAuth credentials

4. **Recovery Worker**:
   - Runs every 2 hours automatically
   - Manual trigger: `gh workflow run recovery_worker.yml`

### 5. Low Pass Rate in Validation

**Symptoms**: "Low pass rate, consider relaxing rules" warning

**Diagnosis**:
```bash
# Check validation results
cat data/metrics/validated_candidates.json | jq '[.[] | select(.passed == true)] | length'

# Check pass rate
cat data/logs/validation_*.log | grep "pass_rate"
```

**Solutions**:
- System automatically relaxes rules if pass rate < 50%
- If persistent:
  - Adjust `config/niche_multipliers.json` to prefer more niches
  - Lower `min_relevance` in validation code
  - Check if trend sources are returning quality data

### 6. Memory Exceeds Limit

**Symptoms**: "Memory limit exceeded" warnings, system slowdown

**Diagnosis**:
```bash
# Check directory sizes
du -sh data/cache data/assets memory

# Check total usage
df -h .
```

**Solutions**:
```bash
# Clear cache
rm -rf data/cache/*

# Prune old memory
python -c "from src.memory import RCIManager; RCIManager().prune_old_records()"

# Compact archives
python scripts/compact_memory.py
```

### 7. No Trends Discovered

**Symptoms**: "Low trend count, adding evergreen" warning

**Diagnosis**:
```bash
# Test each source
python -c "from src.sense import TrendAggregator; a = TrendAggregator(); print(len(a._fetch_reddit()))"
python -c "from src.sense import TrendAggregator; a = TrendAggregator(); print(len(a._fetch_hackernews()))"
python -c "from src.sense import TrendAggregator; a = TrendAggregator(); print(len(a._fetch_news_rss()))"
```

**Solutions**:
1. **Network Issues**: Check internet connectivity
2. **API Rate Limits**: Wait and retry
3. **Source Changes**: Update source URLs in `src/sense/aggregator.py`
4. **Cache Fallback**: System will use cached data automatically
5. **Evergreen Fallback**: System will use evergreen topics as last resort

### 8. Workflow Timeout

**Symptoms**: GitHub Actions job cancelled after 120 minutes

**Diagnosis**:
```bash
# Check workflow duration
gh run view --log | grep "elapsed_minutes"

# Check which step is slow
gh run view --log | grep "STAGE"
```

**Solutions**:
1. **Increase Parallelism**:
   - Edit `config/github_actions_limits.json`
   - Increase `parallelism.shorts_parallel`

2. **Reduce Video Count**:
   - Edit `config/publishing_schedule.json`
   - Reduce `shorts.daily_count`

3. **Optimize Production**:
   - Use simpler EDG templates
   - Reduce video duration
   - Use cached assets

### 9. Safety Violations / Quarantine

**Symptoms**: "Quarantine alert: >10% of daily content" error

**Diagnosis**:
```bash
# Check governor decisions
cat data/metrics/governor_decisions.json

# Check quarantined content
ls -la data/quarantine_artifacts/
```

**Solutions**:
1. **Review Safety Rules**:
   - Edit `config/safety_rules.json`
   - Adjust hard_blocklist and soft_blacklist

2. **Check Trend Sources**:
   - Verify sources aren't returning inappropriate content
   - Add filters in `src/sense/aggregator.py`

3. **Manual Review**:
   - Review quarantined content
   - Update blocklist based on patterns

### 10. Tests Failing

**Symptoms**: `pytest` exits with errors

**Diagnosis**:
```bash
# Run tests with verbose output
pytest -v

# Run specific test
pytest tests/test_sense.py -v

# Check coverage
pytest --cov=src
```

**Solutions**:
1. **Import Errors**:
   ```bash
   pip install -r requirements.txt
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Dependency Issues**:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **Environment Issues**:
   ```bash
   cp .env.example .env
   # Edit .env with test credentials
   ```

## Error Messages Reference

| Error | Meaning | Solution |
|-------|---------|----------|
| `SenseLayerError` | Trend discovery failed | Check network, API keys |
| `ValidationError` | Topic filtering failed | Review validation rules |
| `ScoringError` | VPS calculation failed | Check niche config |
| `GenerationError` | Content creation failed | LLM fallback automatic |
| `ProductionError` | Video assembly failed | Check FFmpeg, assets |
| `PublishingError` | YouTube upload failed | Check OAuth, quota |
| `QuotaExceededError` | API limit reached | Wait for reset |
| `RateLimitError` | Too many requests | Backoff automatic |

## Debug Mode

Enable detailed logging:

```bash
export LOG_LEVEL=DEBUG
cd src
python main.py daily
```

Check logs:
```bash
cat data/logs/*.log | jq 'select(.level == "ERROR")'
```

## Health Check

Run system health check:
```bash
gh workflow run health_check.yml
gh run list --workflow=health_check.yml --limit 1
```

## Support

For issues not covered here:
1. Check GitHub Actions logs
2. Review `data/logs/` for detailed errors
3. Check `data/metrics/daily_summary.json` for status
4. Create GitHub issue with logs and error messages
