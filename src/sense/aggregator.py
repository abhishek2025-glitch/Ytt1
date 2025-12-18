import requests
import feedparser
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from pathlib import Path

from ..shared import (
    get_logger,
    retry_with_backoff,
    handle_errors,
    cache_manager,
    SenseLayerError,
)

logger = get_logger(__name__)

class TrendAggregator:
    def __init__(self):
        self.sources = {
            "finance_rss": self._fetch_finance_rss,
            "reddit_finance": self._fetch_reddit_finance,
        }
        self.evergreen_topics = self._load_evergreen()
        self.archive_path = Path("/home/engine/project/data/sense_archive.json")
        
        logger.info("TrendAggregator initialized", sources=list(self.sources.keys()))
    
    def _load_evergreen(self) -> List[Dict]:
        return [
            {"title": "Stock market tips for beginners", "source": "evergreen", "description": "Fundamental investing advice"},
            {"title": "Dividend investing strategy", "source": "evergreen", "description": "How to build a dividend portfolio"},
            {"title": "Crypto news and trends", "source": "evergreen", "description": "Latest in cryptocurrency"},
            {"title": "Trading strategies meant to work", "source": "evergreen", "description": "Technical analysis basics"},
            {"title": "Market psychology explained", "source": "evergreen", "description": "Fear and greed in markets"},
            {"title": "How the Fed affects your money", "source": "evergreen", "description": "Central bank policy impacts"},
            {"title": "Passive income ideas", "source": "evergreen", "description": "Generating wealth while sleeping"},
            {"title": "Recession survival guide", "source": "evergreen", "description": "Protecting assets during downturns"},
            {"title": "Compound interest magic", "source": "evergreen", "description": "The power of long-term investing"},
            {"title": "ETF vs Individual Stocks", "source": "evergreen", "description": "Diversification strategies"}
        ]
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @handle_errors(fallback_value=[])
    def _fetch_finance_rss(self) -> List[Dict]:
        # Live sources
        cached = cache_manager.get("sense", "finance_rss", max_age_hours=24)
        if cached:
            logger.info("Using cached Finance RSS data")
            return cached
        
        trends = []
        rss_feeds = [
            "https://finance.yahoo.com/news/rssindex",
            "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", # CNBC Finance
            "http://feeds.marketwatch.com/marketwatch/topstories",
            "https://www.investing.com/rss/news_25.rss", # Economic indicators
        ]
        
        for feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:15]:
                    trends.append({
                        "title": entry.get("title", ""),
                        "source": "finance_rss",
                        "source_url": entry.get("link", ""),
                        "description": entry.get("summary", "")[:300],
                        "timestamp": datetime.utcnow().isoformat(),
                        "origin_count": 1,
                    })
            except Exception as e:
                logger.warning(f"RSS fetch error for {feed_url}", error=str(e))
        
        if trends:
            cache_manager.set("sense", "finance_rss", trends, ttl_hours=24)
            logger.info("Finance RSS trends fetched", count=len(trends))
        return trends
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @handle_errors(fallback_value=[])
    def _fetch_reddit_finance(self) -> List[Dict]:
        cached = cache_manager.get("sense", "reddit_finance", max_age_hours=24)
        if cached:
            logger.info("Using cached Reddit Finance data")
            return cached
        
        trends = []
        subreddits = ["stocks", "investing", "cryptocurrency", "finance", "wallstreetbets", "financialindependence"]
        
        for subreddit in subreddits:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json"
                headers = {"User-Agent": "ViralosPrime/2.0"}
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get("data", {}).get("children", [])
                    
                    for post in posts[:10]:
                        post_data = post.get("data", {})
                        if post_data.get("stickied"): continue
                        
                        trends.append({
                            "title": post_data.get("title", ""),
                            "source": "reddit",
                            "source_url": f"https://reddit.com{post_data.get('permalink', '')}",
                            "description": post_data.get("selftext", "")[:300],
                            "timestamp": datetime.utcnow().isoformat(),
                            "origin_count": 1,
                            "score": post_data.get("score", 0),
                        })
                
                time.sleep(1.0) # Respect rate limits
            except Exception as e:
                logger.warning(f"Reddit fetch error for r/{subreddit}", error=str(e))
        
        if trends:
            cache_manager.set("sense", "reddit_finance", trends, ttl_hours=24)
            logger.info("Reddit Finance trends fetched", count=len(trends))
        return trends
        
    def _get_archived_trends(self) -> List[Dict]:
        """Retrieve trends from the 7-day archive"""
        try:
            if not self.archive_path.exists():
                return []
                
            with open(self.archive_path, 'r') as f:
                archive = json.load(f)
            
            # Filter for last 7 days
            cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
            valid_items = [item for item in archive if item.get('timestamp') > cutoff]
            
            logger.info(f"Retrieved {len(valid_items)} trends from archive")
            return valid_items
        except Exception as e:
            logger.error("Failed to read archive", error=str(e))
            return []

    def _update_archive(self, trends: List[Dict]):
        """Update the 7-day archive with new trends"""
        try:
            existing = []
            if self.archive_path.exists():
                with open(self.archive_path, 'r') as f:
                    existing = json.load(f)
            
            # Combine and dedup by title
            seen_titles = {item['title'] for item in existing}
            for trend in trends:
                if trend['title'] not in seen_titles:
                    existing.append(trend)
                    seen_titles.add(trend['title'])
            
            # Prune old
            cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
            existing = [item for item in existing if item.get('timestamp') > cutoff]
            
            # Ensure directory exists
            self.archive_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.archive_path, 'w') as f:
                json.dump(existing, f)
        except Exception as e:
            logger.error("Failed to update archive", error=str(e))

    def aggregate_all(self) -> List[Dict]:
        all_trends = []
        
        # 1. Try Live Sources
        for source_name, fetch_func in self.sources.items():
            try:
                trends = fetch_func()
                if trends:
                    all_trends.extend(trends)
                    logger.info(f"Aggregated from {source_name}", count=len(trends))
            except Exception as e:
                logger.error(f"Failed to aggregate from {source_name}", error=str(e))
        
        # 2. Fallback to 48h Cache (handled inside fetch functions essentially, but we can check if all_trends is empty)
        # The fetch functions check cache first. If they return empty/fail, we move to step 3.
        
        # 3. Fallback to 7-day Archive
        if len(all_trends) < 10:
            logger.warning("Low live trend count, checking archive", current=len(all_trends))
            archived = self._get_archived_trends()
            # Randomly sample or take latest from archive to fill up
            needed = 20 - len(all_trends)
            if needed > 0 and archived:
                # Simple strategy: take most recent not already present
                current_titles = {t['title'] for t in all_trends}
                added_count = 0
                for item in sorted(archived, key=lambda x: x['timestamp'], reverse=True):
                    if item['title'] not in current_titles:
                        all_trends.append(item)
                        added_count += 1
                        if added_count >= needed:
                            break
        
        # 4. Fallback to Evergreen
        if len(all_trends) < 5:
            logger.warning("Critical low trend count, adding evergreen", current=len(all_trends))
            all_trends.extend(self.evergreen_topics)
            
        # Update archive with whatever we found (if it's fresh)
        self._update_archive(all_trends)
        
        # Add IDs
        for i, trend in enumerate(all_trends):
            if "id" not in trend:
                trend["id"] = f"trend_{int(time.time())}_{i}"
        
        logger.info("Total trends aggregated", count=len(all_trends))
        return all_trends
