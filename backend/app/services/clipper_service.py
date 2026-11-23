import os
import re
import json
import uuid
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Callable
import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

logger = logging.getLogger(__name__)

class ClipperEngine:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.audio_dir = data_dir / "audio"
        self.clips_dir = data_dir / "clips"
        self.thumbs_dir = data_dir / "thumbnails"
        
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.clips_dir.mkdir(parents=True, exist_ok=True)
        self.thumbs_dir.mkdir(parents=True, exist_ok=True)

    def extract_vod_id(self, url: str) -> str | None:
        match = re.search(r"videos/(\d+)", url)
        if match:
            return match.group(1)
        # Check YouTube video id
        yt_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
        if yt_match:
            return yt_match.group(1)
        return None

    def get_stream_urls(self, url: str) -> Dict[str, str]:
        """Fetch direct audio and video URLs using yt-dlp without downloading full files."""
        cmd = ["yt-dlp", "-g", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best", url]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
            if len(lines) >= 2:
                return {"video": lines[0], "audio": lines[1]}
            elif len(lines) == 1:
                return {"video": lines[0], "audio": lines[0]}
        except Exception as e:
            logger.warning(f"Failed to get direct stream URL: {e}. Will attempt direct download.")
        return {}

    def extract_audio_from_source(self, source_url: str, job_id: str) -> Path:
        """Extract 16kHz mono WAV from source URL or local file."""
        output_wav = self.audio_dir / f"{job_id}.wav"
        if output_wav.exists():
            return output_wav

        # Use ffmpeg directly with yt-dlp pipe or directly on file/URL
        cmd = [
            "ffmpeg",
            "-i", source_url,
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-sample_fmt", "s16",
            "-y",
            str(output_wav)
        ]
        logger.info(f"Extracting audio to {output_wav}...")
        subprocess.run(cmd, check=True, capture_output=True)
        return output_wav

    def compute_loudness_envelope(self, wav_path: Path, hop_size: int = 1600) -> tuple[np.ndarray, np.ndarray]:
        """
        Compute loudness envelope from 16kHz PCM WAV.
        hop_size = 1600 samples = 0.1s resolution (10 frames/sec)
        """
        # Read raw PCM data from WAV
        with open(wav_path, "rb") as f:
            # Skip 44-byte WAV header
            f.seek(44)
            data = np.frombuffer(f.read(), dtype=np.int16).astype(np.float32)

        if len(data) == 0:
            return np.array([]), np.array([])

        num_frames = len(data) // hop_size
        rms_values = np.zeros(num_frames, dtype=np.float32)
        for i in range(num_frames):
            frame = data[i * hop_size : (i + 1) * hop_size]
            rms_values[i] = np.sqrt(np.mean(frame ** 2) + 1e-8)

        times = np.arange(num_frames) * (hop_size / 16000.0)
        return times, rms_values

    def detect_peak_windows(
        self,
        times: np.ndarray,
        rms: np.ndarray,
        clip_padding: float = 15.0,
        prominence_thresh: float = 0.8,
        min_distance_sec: float = 15.0
    ) -> List[Dict[str, Any]]:
        """Detect audio energy peaks and form clip candidate windows."""
        if len(rms) == 0:
            return []

        # Standardize (Z-score)
        std = np.std(rms)
        if std == 0:
            return []
        norm_rms = (rms - np.mean(rms)) / std

        # Smooth signal
        smoothed = gaussian_filter1d(norm_rms, sigma=1.0)
        dt = times[1] - times[0] if len(times) > 1 else 0.1
        min_dist_frames = int(min_distance_sec / dt)

        peaks, props = find_peaks(
            smoothed,
            prominence=prominence_thresh,
            distance=min_dist_frames
        )

        candidates = []
        max_time = times[-1]
        for p, prom in zip(peaks, props["prominences"]):
            peak_time = times[p]
            start_t = max(0.0, peak_time - clip_padding)
            end_t = min(max_time, peak_time + clip_padding)
            candidates.append({
                "start": start_t,
                "end": end_t,
                "peak_time": peak_time,
                "score": float(prom),
                "loudness_score": float(prom)
            })

        # Sort by score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates

    def cut_clip(
        self,
        source: str,
        start_sec: float,
        duration_sec: float,
        output_path: Path,
        vertical: bool = True
    ) -> Path:
        """Cut and encode clip to 9:16 vertical or original aspect ratio."""
        filters = []
        if vertical:
            # Smart 9:16 crop & scale to 1080x1920
            filters.append("crop=ih*9/16:ih,scale=1080:1920")
        
        # Add smooth fade in/out
        fade_dur = 0.4
        fade_out_st = max(0.0, duration_sec - fade_dur)
        filters.append(f"fade=t=in:d={fade_dur},fade=t=out:st={fade_out_st}:d={fade_dur}")
        vf_string = ",".join(filters)

        cmd = [
            "ffmpeg",
            "-ss", f"{start_sec:.2f}",
            "-i", source,
            "-t", f"{duration_sec:.2f}",
            "-vf", vf_string,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "160k",
            "-avoid_negative_ts", "make_zero",
            "-y",
            str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    def generate_thumbnail(self, video_path: Path, output_thumb: Path) -> Path:
        """Extract a frame from the middle of the clip as a thumbnail."""
        cmd = [
            "ffmpeg",
            "-ss", "00:00:02",
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "3",
            "-y",
            str(output_thumb)
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except Exception:
            pass
        return output_thumb

    def process_job(
        self,
        job_id: str,
        vod_url: str,
        max_clips: int = 5,
        vertical: bool = True,
        clip_padding: float = 15.0,
        progress_callback: Callable[[int, str], None] = None
    ) -> List[Dict[str, Any]]:
        """Orchestrates the entire extraction, peak detection, and clipping pipeline."""
        if progress_callback:
            progress_callback(10, "Fetching media source stream...")

        # If it's a local file
        local_path = Path(vod_url)
        if local_path.exists():
            media_source = str(local_path.resolve())
        else:
            # Check for direct stream URLs
            stream_urls = self.get_stream_urls(vod_url)
            media_source = stream_urls.get("video", vod_url)

        if progress_callback:
            progress_callback(30, "Extracting audio & analyzing acoustic envelope...")

        wav_path = self.extract_audio_from_source(media_source, job_id)
        times, rms = self.compute_loudness_envelope(wav_path)

        if progress_callback:
            progress_callback(55, "Detecting energy peaks & candidate windows...")

        candidates = self.detect_peak_windows(
            times, rms,
            clip_padding=clip_padding,
            prominence_thresh=0.7,
            min_distance_sec=20.0
        )

        top_candidates = candidates[:max_clips]
        if not top_candidates:
            logger.warning("No high-prominence peaks detected.")
            return []

        if progress_callback:
            progress_callback(70, f"Generating {len(top_candidates)} 9:16 vertical clips...")

        job_clips_dir = self.clips_dir / job_id
        job_clips_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for idx, cand in enumerate(top_candidates, start=1):
            clip_id = f"clip_{idx:02d}"
            dur = cand["end"] - cand["start"]
            out_clip = job_clips_dir / f"{clip_id}.mp4"
            out_thumb = self.thumbs_dir / f"{job_id}_{clip_id}.jpg"

            self.cut_clip(
                media_source,
                start_sec=cand["start"],
                duration_sec=dur,
                output_path=out_clip,
                vertical=vertical
            )
            self.generate_thumbnail(out_clip, out_thumb)

            viral_categories = ["Hype Reaction", "Excited Screaming", "Intense Gameplay", "Clutch Moment"]
            category = viral_categories[(idx - 1) % len(viral_categories)]

            results.append({
                "id": str(uuid.uuid4()),
                "job_id": job_id,
                "title": f"Viral Highlight #{idx}",
                "start_time": cand["start"],
                "end_time": cand["end"],
                "duration": dur,
                "score": round(cand["score"], 2),
                "dominant_signal": "Acoustic Loudness Spike",
                "viral_category": category,
                "keywords": ["hype", "insane", "reaction"],
                "video_url": f"/api/v1/clips/stream/{job_id}/{clip_id}.mp4",
                "thumbnail_url": f"/api/v1/clips/thumb/{job_id}_{clip_id}.jpg",
                "is_vertical": vertical
            })

            if progress_callback:
                pct = 70 + int((idx / len(top_candidates)) * 25)
                progress_callback(pct, f"Finished rendering clip #{idx}...")

        if progress_callback:
            progress_callback(100, "All clips successfully generated!")

        return results
