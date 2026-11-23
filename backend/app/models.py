from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime

class ClipSubmitRequest(BaseModel):
    vod_url: str
    max_clips: int = 5
    min_score: float = 0.5
    vertical: bool = True
    clip_padding: float = 15.0  # seconds around peak (30s clip)

class ClipInfo(BaseModel):
    id: str
    job_id: str
    title: str
    start_time: float
    end_time: float
    duration: float
    score: float
    dominant_signal: str
    viral_category: str
    keywords: List[str] = []
    video_url: str
    thumbnail_url: Optional[str] = None
    is_vertical: bool = True
    created_at: datetime = datetime.now()

class JobStatusResponse(BaseModel):
    job_id: str
    vod_url: str
    status: str  # QUEUED, DOWNLOADING, ANALYZING, TRANSCRIBING, CLIPPING, COMPLETED, FAILED
    progress_percent: int = 0
    current_step: str = "Initialized"
    error_message: Optional[str] = None
    clips: List[ClipInfo] = []
    created_at: datetime = datetime.now()
