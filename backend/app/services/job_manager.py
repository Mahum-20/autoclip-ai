import asyncio
import uuid
import logging
from typing import Dict, List, Set
from fastapi import WebSocket
from ..models import JobStatusResponse, ClipInfo
from .clipper_service import ClipperEngine

logger = logging.getLogger(__name__)

class JobManager:
    def __init__(self, clipper_engine: ClipperEngine):
        self.engine = clipper_engine
        self.jobs: Dict[str, JobStatusResponse] = {}
        self.active_websockets: Dict[str, Set[WebSocket]] = {}

    def create_job(self, vod_url: str) -> str:
        job_id = str(uuid.uuid4())[:8]
        self.jobs[job_id] = JobStatusResponse(
            job_id=job_id,
            vod_url=vod_url,
            status="QUEUED",
            progress_percent=0,
            current_step="Job queued for processing",
            clips=[]
        )
        self.active_websockets[job_id] = set()
        return job_id

    def get_job(self, job_id: str) -> JobStatusResponse | None:
        return self.jobs.get(job_id)

    async def register_websocket(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        if job_id not in self.active_websockets:
            self.active_websockets[job_id] = set()
        self.active_websockets[job_id].add(websocket)

    def unregister_websocket(self, job_id: str, websocket: WebSocket):
        if job_id in self.active_websockets:
            self.active_websockets[job_id].discard(websocket)

    async def broadcast_progress(self, job_id: str, percent: int, step: str):
        job = self.jobs.get(job_id)
        if job:
            job.progress_percent = percent
            job.current_step = step

        if job_id in self.active_websockets:
            disconnected = set()
            for ws in self.active_websockets[job_id]:
                try:
                    await ws.send_json({
                        "job_id": job_id,
                        "progress_percent": percent,
                        "current_step": step,
                        "status": job.status if job else "PROCESSING"
                    })
                except Exception:
                    disconnected.add(ws)
            for ws in disconnected:
                self.active_websockets[job_id].discard(ws)

    async def run_job_async(self, job_id: str, max_clips: int, vertical: bool, clip_padding: float):
        job = self.jobs.get(job_id)
        if not job:
            return

        job.status = "PROCESSING"
        loop = asyncio.get_running_loop()

        def sync_progress(percent: int, step: str):
            asyncio.run_coroutine_threadsafe(
                self.broadcast_progress(job_id, percent, step),
                loop
            )

        try:
            clips_data = await asyncio.to_thread(
                self.engine.process_job,
                job_id=job_id,
                vod_url=job.vod_url,
                max_clips=max_clips,
                vertical=vertical,
                clip_padding=clip_padding,
                progress_callback=sync_progress
            )

            job.clips = [ClipInfo(**c) for c in clips_data]
            job.status = "COMPLETED"
            job.progress_percent = 100
            job.current_step = f"Completed! Generated {len(job.clips)} viral clips."
            await self.broadcast_progress(job_id, 100, job.current_step)

        except Exception as e:
            logger.exception(f"Job {job_id} failed: {e}")
            job.status = "FAILED"
            job.error_message = str(e)
            job.current_step = f"Error: {e}"
            await self.broadcast_progress(job_id, job.progress_percent, f"Failed: {e}")
