import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from ..shared import get_logger, handle_errors

logger = get_logger(__name__)

class TTSGenerator:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_audio(self, text: str, voice: str = "default") -> Optional[Path]:
        # Fallback Chain: Kokoro -> Piper -> eSpeak -> Captions (None)
        
        # 1. Try Kokoro (Simulated)
        if self._try_kokoro(text):
            return self.output_dir / "tts_kokoro.wav"
            
        # 2. Try Piper (Simulated)
        if self._try_piper(text):
            return self.output_dir / "tts_piper.wav"
            
        # 3. Try eSpeak (Simulated)
        if self._try_espeak(text):
            return self.output_dir / "tts_espeak.wav"
            
        # 4. Fallback to Captions (return None, implied silence)
        logger.warning("All TTS engines failed, falling back to captions-only")
        return self._generate_silence(duration=5.0) # Dummy silence
    
    def _try_kokoro(self, text: str) -> bool:
        # Simulate check
        return False # Not installed
        
    def _try_piper(self, text: str) -> bool:
        return False # Not installed
        
    def _try_espeak(self, text: str) -> bool:
        return False # Not installed
    
    def _generate_silence(self, duration: float) -> Optional[Path]:
        output_path = self.output_dir / "silence.wav"
        try:
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono", 
                "-t", str(duration), str(output_path)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except:
            return None

class ThumbnailGenerator:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_variants(self, video_id: str, title: str) -> List[Dict]:
        variants = []
        for i, style in enumerate(["high_contrast", "emotional", "data_driven"]):
            path = self.output_dir / f"{video_id}_thumb_v{i+1}.jpg"
            if self._create_dummy_thumbnail(path, title, style):
                variants.append({
                    "path": str(path),
                    "style": style,
                    "variant_id": f"v{i+1}"
                })
        return variants
    
    def _create_dummy_thumbnail(self, path: Path, title: str, style: str) -> bool:
        try:
            # Create a simple color image with text using ffmpeg
            color = "red" if style == "high_contrast" else "green" if style == "emotional" else "blue"
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={color}:s=1280x720",
                "-frames:v", "1", str(path)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except Exception as e:
            logger.error("Thumbnail generation failed", error=str(e))
            return False

class VideoAssembler:
    def __init__(self):
        self.output_dir = Path("data/assets/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tts = TTSGenerator(self.output_dir / "audio")
        self.thumb_gen = ThumbnailGenerator(self.output_dir / "thumbnails")
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
        
        # 1. Generate TTS
        # In a real run, we'd loop through scenes. Here simplified.
        script = edg.get("metadata", {}).get("script_full", "")
        audio_path = self.tts.generate_audio(script[:100]) # Sample
        
        # 2. Assemble Video
        success = self._create_ffmpeg_video(edg, output_path, audio_path)
        
        # 3. Generate Thumbnails
        thumbnails = self.thumb_gen.generate_variants(video_id, edg.get("metadata", {}).get("titles", ["Video"])[0])
        
        if success and output_path.exists():
            logger.info("Video assembled successfully", path=str(output_path), thumbnails=len(thumbnails))
            return str(output_path)
        else:
            logger.error("Video assembly failed")
            return None
    
    def _create_ffmpeg_video(self, edg: Dict, output_path: Path, audio_path: Optional[Path]) -> bool:
        try:
            duration = edg.get("duration_seconds", 28)
            aspect_ratio = edg.get("aspect_ratio", "9:16")
            
            if aspect_ratio == "9:16":
                width, height = 1080, 1920
            else:
                width, height = 1920, 1080
            
            color = "#1a1a2e"
            
            inputs = ["-f", "lavfi", "-i", f"color=c={color}:s={width}x{height}:d={duration}"]
            
            if audio_path and audio_path.exists():
                inputs.extend(["-i", str(audio_path)])
                # Mix audio if present
                maps = ["-map", "0:v", "-map", "1:a"]
            else:
                maps = ["-map", "0:v"]
            
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                *inputs,
                "-vf", f"drawtext=text='VIRALOS PRIME':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-t", str(duration),
                *maps,
                str(output_path)
            ]
            
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=120
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
