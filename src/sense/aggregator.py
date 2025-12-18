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
            "reddit": self._fetch_reddit,
            "hackernews": self._fetch_hackernews,
            "news_rss": self._fetch_news_rss,
        }
        self.evergreen_topics = self._load_evergreen()
        
        logger.info("TrendAggregator initialized", sources=list(self.sources.keys()))
    
    def _load_evergreen(self) -> List[Dict]:
        return [
            {"title": "AI replacing jobs", "source": "evergreen", "description": "Impact of AI on employment"},
            {"title": "Passive income strategies", "source": "evergreen", "description": "Building passive income streams"},
            {"title": "Market volatility patterns", "source": "evergreen", "description": "Understanding market cycles"},
            {"title": "Productivity myths debunked", "source": "evergreen", "description": "Common productivity misconceptions"},
            {"title": "Cryptocurrency regulation", "source": "evergreen", "description": "Crypto regulatory landscape"},
        ]
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @handle_errors(fallback_value=[])
    def _fetch_reddit(self) -> List[Dict]:
        cached = cache_manager.get("sense", "reddit", max_age_hours=24)
        if cached:
            logger.info("Using cached Reddit data")
            return cached
        
        trends = []
        subreddits = ["technology", "business", "finance", "artificial", "Futurology"]
        
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
                        trends.append({
                            "title": post_data.get("title", ""),
                            "source": "reddit",
                            "source_url": f"https://reddit.com{post_data.get('permalink', '')}",
                            "description": post_data.get("selftext", "")[:200],
                            "timestamp": datetime.utcnow().isoformat(),
                            "origin_count": 1,
                            "score": post_data.get("score", 0),
                        })
                
                time.sleep(0.5)
            except Exception as e:
                logger.warning(f"Reddit fetch error for r/{subreddit}", error=str(e))
        
        cache_manager.set("sense", "reddit", trends, ttl_hours=24)
        logger.info("Reddit trends fetched", count=len(trends))
        return trends
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @handle_errors(fallback_value=[])
    def _fetch_hackernews(self) -> List[Dict]:
        cached = cache_manager.get("sense", "hackernews", max_age_hours=24)
        if cached:
            logger.info("Using cached HackerNews data")
            return cached
        
        trends = []
        
        try:
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                story_ids = response.json()[:30]
                
                for story_id in story_ids:
                    try:
                        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                        story_response = requests.get(story_url, timeout=5)
                        
                        if story_response.status_code == 200:
                            story = story_response.json()
                            trends.append({
                                "title": story.get("title", ""),
                                "source": "hackernews",
                                "source_url": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                                "description": story.get("text", "")[:200] if story.get("text") else "",
                                "timestamp": datetime.utcnow().isoformat(),
                                "origin_count": 1,
                                "score": story.get("score", 0),
                            })
                        
                        time.sleep(0.1)
                    except:
                        continue
        except Exception as e:
            logger.warning("HackerNews fetch error", error=str(e))
        
        cache_manager.set("sense", "hackernews", trends, ttl_hours=24)
        logger.info("HackerNews trends fetched", count=len(trends))
        return trends
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @handle_errors(fallback_value=[])
    def _fetch_news_rss(self) -> List[Dict]:
        cached = cache_manager.get("sense", "news_rss", max_age_hours=24)
        if cached:
            logger.info("Using cached RSS news data")
            return cached
        
        trends = []
        rss_feeds = [
            "http://feeds.bbci.co.uk/news/rss.xml",
            "https://www.reuters.com/rssFeed/businessNews",
        ]
        
        for feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:15]:
                    trends.append({
                        "title": entry.get("title", ""),
                        "source": "news_rss",
                        "source_url": entry.get("link", ""),
                        "description": entry.get("summary", "")[:200],
                        "timestamp": datetime.utcnow().isoformat(),
                        "origin_count": 1,
                    })
            except Exception as e:
                logger.warning(f"RSS fetch error for {feed_url}", error=str(e))
        
        cache_manager.set("sense", "news_rss", trends, ttl_hours=24)
        logger.info("RSS news trends fetched", count=len(trends))
        return trends
    
    def aggregate_all(self) -> List[Dict]:
        all_trends = []
        
        for source_name, fetch_func in self.sources.items():
            try:
                trends = fetch_func()
                all_trends.extend(trends)
                logger.info(f"Aggregated from {source_name}", count=len(trends))
            except Exception as e:
                logger.error(f"Failed to aggregate from {source_name}", error=str(e))
                
                cached = cache_manager.get("sense", f"{source_name}_12h", max_age_hours=12)
                if cached:
                    logger.info(f"Using older cache for {source_name}")
                    all_trends.extend(cached)
        
        if len(all_trends) < 20:
            logger.warning("Low trend count, adding evergreen", current=len(all_trends))
            all_trends.extend(self.evergreen_topics)
        
        for i, trend in enumerate(all_trends):
            if "id" not in trend:
                trend["id"] = f"trend_{int(time.time())}_{i}"
        
        logger.info("Total trends aggregated", count=len(all_trends))
        return all_trends
