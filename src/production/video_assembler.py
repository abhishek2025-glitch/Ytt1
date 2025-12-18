import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional
from ..shared import get_logger, handle_errors

logger = get_logger(__name__)

class VideoAssembler:
    def __init__(self):
        self.output_dir = Path("data/assets/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("VideoAssembler initialized")
    
    def check_ffmpeg(self) -> bool:
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            available = result.returncode == 0
            logger.info("FFmpeg check", available=available)
            return available
        except:
            logger.warning("FFmpeg not available")
            return False
    
    @handle_errors(fallback_value=None)
    def assemble_video(self, edg: Dict, assets: List[Dict]) -> Optional[str]:
        video_id = edg.get("video_id", "unknown")
        format_type = edg.get("format", "short")
        
        logger.info("Assembling video", video_id=video_id, format=format_type)
        
        if not self.check_ffmpeg():
            logger.error("FFmpeg not available, cannot assemble video")
            return self._create_placeholder_video(video_id, format_type)
        
        output_path = self.output_dir / f"{video_id}.mp4"
        
        success = self._create_simple_video(edg, output_path)
        
        if success and output_path.exists():
            logger.info("Video assembled successfully", path=str(output_path))
            return str(output_path)
        else:
            logger.error("Video assembly failed")
            return None
    
    def _create_simple_video(self, edg: Dict, output_path: Path) -> bool:
        try:
            duration = edg.get("duration_seconds", 28)
            aspect_ratio = edg.get("aspect_ratio", "9:16")
            
            if aspect_ratio == "9:16":
                width, height = 1080, 1920
            else:
                width, height = 1920, 1080
            
            color = "#1a1a2e"
            
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-f", "lavfi",
                "-i", f"color=c={color}:s={width}x{height}:d={duration}",
                "-vf", f"drawtext=text='VIRALOS PRIME':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-t", str(duration),
                str(output_path)
            ]
            
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("FFmpeg video created", output=str(output_path))
                return True
            else:
                logger.error("FFmpeg failed", stderr=result.stderr[:200])
                return False
        
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timeout")
            return False
        except Exception as e:
            logger.error("FFmpeg error", error=str(e))
            return False
    
    def _create_placeholder_video(self, video_id: str, format_type: str) -> Optional[str]:
        output_path = self.output_dir / f"{video_id}_placeholder.txt"
        
        with open(output_path, 'w') as f:
            f.write(f"Placeholder for video: {video_id}\nFormat: {format_type}\n")
        
        logger.info("Placeholder created", path=str(output_path))
        return str(output_path)
    
    def batch_assemble(self, content_items: List[Dict]) -> List[Dict]:
        results = []
        
        for item in content_items:
            edg = item.get("edg", {})
            video_path = self.assemble_video(edg, [])
            
            results.append({
                "video_id": edg.get("video_id"),
                "video_path": video_path,
                "status": "success" if video_path else "failed",
                "metadata": item.get("metadata", {}),
            })
        
        logger.info("Batch assembly complete", total=len(results), success=sum(1 for r in results if r["status"] == "success"))
        return results
