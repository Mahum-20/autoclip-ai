import os
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import ClipSubmitRequest, JobStatusResponse
from .services.clipper_service import ClipperEngine
from .services.job_manager import JobManager

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

app = FastAPI(
    title="Auto-Clipping API",
    description="Backend engine for AI Stream & VOD Auto-Clipping",
    version="1.0.0"
)

# Enable CORS for Android client & Mobile Web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ClipperEngine(DATA_DIR)
job_manager = JobManager(engine)

@app.post("/api/v1/jobs/submit", response_model=JobStatusResponse)
async def submit_clip_job(request: ClipSubmitRequest, background_tasks: BackgroundTasks):
    """Submit a Twitch / YouTube VOD URL for automatic clipping."""
    job_id = job_manager.create_job(request.vod_url)
    
    # Run pipeline in background
    background_tasks.add_task(
        job_manager.run_job_async,
        job_id=job_id,
        max_clips=request.max_clips,
        vertical=request.vertical,
        clip_padding=request.clip_padding
    )
    
    job = job_manager.get_job(job_id)
    return job

@app.get("/api/v1/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Poll job status and get generated clips."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.websocket("/ws/jobs/{job_id}/progress")
async def websocket_job_progress(websocket: WebSocket, job_id: str):
    """Real-time WebSocket connection to stream pipeline progress updates."""
    await job_manager.register_websocket(job_id, websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        job_manager.unregister_websocket(job_id, websocket)

@app.get("/api/v1/clips/stream/{job_id}/{clip_filename}")
async def stream_clip(job_id: str, clip_filename: str):
    """Stream video clip with partial content support."""
    clip_path = DATA_DIR / "clips" / job_id / clip_filename
    if not clip_path.exists():
        raise HTTPException(status_code=404, detail="Clip video file not found")
    return FileResponse(clip_path, media_type="video/mp4")

@app.get("/api/v1/clips/thumb/{thumb_filename}")
async def get_thumbnail(thumb_filename: str):
    """Serve video thumbnail frame."""
    thumb_path = DATA_DIR / "thumbnails" / thumb_filename
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(thumb_path, media_type="image/jpeg")

# Mount web_mobile static folder if it exists
web_dir = BASE_DIR.parent / "web_mobile"
if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web_mobile")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
