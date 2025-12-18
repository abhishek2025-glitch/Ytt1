from typing import List, Dict
from ..shared import get_logger, embedding_service

logger = get_logger(__name__)

class SemanticDeduplicator:
    def __init__(self, similarity_threshold: float = 0.75):
        self.similarity_threshold = similarity_threshold
        logger.info("SemanticDeduplicator initialized", threshold=similarity_threshold)
    
    def deduplicate(self, trends: List[Dict]) -> List[Dict]:
        if not trends:
            return []
        
        texts = [f"{t.get('title', '')} {t.get('description', '')}" for t in trends]
        
        clusters = embedding_service.cluster_by_similarity(texts, self.similarity_threshold)
        
        deduplicated = []
        for cluster in clusters:
            representative_idx = cluster[0]
            representative = trends[representative_idx].copy()
            
            representative["origin_count"] = len(cluster)
            
            if len(cluster) > 1:
                sources = list(set(trends[i].get("source", "") for i in cluster))
                representative["consensus_sources"] = sources
                representative["cluster_size"] = len(cluster)
            
            deduplicated.append(representative)
        
        logger.info(
            "Deduplication complete",
            input_count=len(trends),
            output_count=len(deduplicated),
            reduction_pct=round((1 - len(deduplicated)/len(trends)) * 100, 1)
        )
        
        return deduplicated
    
    def merge_origins(self, trends: List[Dict]) -> List[Dict]:
        title_map = {}
        
        for trend in trends:
            title = trend.get("title", "").lower().strip()
            if title:
                if title not in title_map:
                    title_map[title] = trend.copy()
                    title_map[title]["origin_count"] = 1
                    title_map[title]["sources"] = [trend.get("source")]
                else:
                    title_map[title]["origin_count"] += 1
                    title_map[title]["sources"].append(trend.get("source"))
                    title_map[title]["sources"] = list(set(title_map[title]["sources"]))
        
        merged = list(title_map.values())
        logger.info("Origin merge complete", input=len(trends), output=len(merged))
        
        return merged
