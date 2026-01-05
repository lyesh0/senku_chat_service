"""FastAPI server for Qwen model fine‑tuning service.

This server provides REST API endpoints for starting fine‑tuning jobs,
checking training status, and downloading trained models.  For test
environments or when FastAPI and other heavy dependencies are not
installed, the module degrades gracefully: it still exposes the same
names (e.g. ``app``, ``TrainingRequest``) but does not attempt to import
FastAPI or register any routes.

"""

import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

# Attempt to import FastAPI and related types; fall back to no‑op stubs
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks  # type: ignore
    from fastapi.middleware.cors import CORSMiddleware  # type: ignore
    from pydantic import BaseModel  # type: ignore
    _FASTAPI_AVAILABLE = True
except Exception:
    # FastAPI or Pydantic not available; provide minimal fallbacks
    FastAPI = None  # type: ignore
    class HTTPException(Exception):
        """Minimal HTTPException replacement when FastAPI is unavailable."""
        def __init__(self, status_code: int = 500, detail: str = ""):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail
    BackgroundTasks = None  # type: ignore
    CORSMiddleware = None  # type: ignore
    class BaseModel:  # type: ignore
        """Placeholder base model when Pydantic is unavailable."""
        pass
    _FASTAPI_AVAILABLE = False

# Import local modules lazily; if they fail to import, the names will be None.
try:
    from .fine_tune import start_fine_tuning  # type: ignore
except Exception:
    start_fine_tuning = None  # type: ignore
try:
    from .storage import upload_model, download_model  # type: ignore
except Exception:
    upload_model = download_model = None  # type: ignore
try:
    from .ssh_manager import get_ssh_manager, connect_ssh, disconnect_ssh, TrainingConfig  # type: ignore
except Exception:
    get_ssh_manager = connect_ssh = disconnect_ssh = None  # type: ignore
    TrainingConfig = None  # type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global storage for training jobs (in production, use a database)
training_jobs: Dict[str, Dict] = {}

if _FASTAPI_AVAILABLE and FastAPI is not None:
    # Instantiate FastAPI application
    app = FastAPI(title="Qwen Fine‑tuning API", version="1.0.0")
    # Optional: add CORS middleware if available
    if CORSMiddleware is not None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Define request/response models using Pydantic
    class TrainingRequest(BaseModel):
        """Request payload for starting a fine‑tuning job."""
        role: str  # Role configuration file name (e.g., "luffy.json")
        batch_size: int = 32
        epochs: int = 3
        training_mode: str = "local"  # "local" or "remote"
        use_lora: bool = True

    class TrainingResponse(BaseModel):
        status: str
        model_id: str
        message: str

    class StatusResponse(BaseModel):
        status: str  # "pending", "running", "completed", "failed"
        progress: Optional[Dict] = None
        epochs_completed: Optional[int] = None
        total_epochs: Optional[int] = None
        error: Optional[str] = None

    class DownloadResponse(BaseModel):
        status: str
        download_link: Optional[str] = None
        error: Optional[str] = None

    class SSHStatusResponse(BaseModel):
        connected: bool
        hostname: Optional[str] = None
        error: Optional[str] = None

    @app.on_event("startup")
    async def startup_event():
        """Initialize the server by creating the models directory."""
        logger.info("Qwen Fine‑tuning API server starting up…")
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        logger.info("Server ready to accept requests.")

    @app.get("/health")
    async def health_check():
        """Health check endpoint returning service status."""
        return {"status": "healthy", "service": "qwen‑finetuning‑api"}

    # ------------------------------------------------------------------
    # Training endpoints
    # ------------------------------------------------------------------

    def _generate_model_id() -> str:
        """Generate a unique model identifier for a new training job."""
        return uuid.uuid4().hex

    def _record_job(model_id: str, job_info: Dict) -> None:
        """Record training job information in memory.

        Parameters
        ----------
        model_id : str
            Unique identifier for the training job.
        job_info : Dict
            Metadata describing the training job (e.g., mode, epochs, role).
        """
        training_jobs[model_id] = job_info

    @app.post("/train", response_model=TrainingResponse)
    async def train_model(request: TrainingRequest, background_tasks: BackgroundTasks):
        """Start a new fine‑tuning job.

        Supports both local and remote training modes.  In local mode the
        server will execute fine‑tuning directly (requires torch/transformers).
        In remote mode the server will dispatch the job to a configured SSH
        host via the ``ssh_manager`` module.

        Parameters
        ----------
        request : TrainingRequest
            Request body containing training parameters.

        Returns
        -------
        TrainingResponse
            Information about the initiated job.
        """
        model_id = _generate_model_id()
        role_file_path = Path("roles") / request.role
        if not role_file_path.exists():
            raise HTTPException(status_code=400, detail=f"Role not found: {request.role}")

        # Handle remote training
        if request.training_mode == "remote":
            if TrainingConfig is None or get_ssh_manager is None:
                raise HTTPException(status_code=503, detail="Remote training is unavailable in this environment")

            manager = get_ssh_manager()
            if not manager:
                raise HTTPException(status_code=503, detail="SSH manager is not configured")

            # Build remote training configuration
            remote_config = TrainingConfig(
                model_id=model_id,
                role_file=str(role_file_path),
                batch_size=request.batch_size,
                epochs=request.epochs,
                learning_rate=2e-5,  # Default LR; could be parameterized
                use_lora=request.use_lora
            )

            # Ensure SSH connection is established
            if not manager.connect():
                raise HTTPException(status_code=503, detail="Failed to connect to remote server")

            try:
                job_id = manager.start_training(remote_config)
            except Exception as exc:
                # Disconnect on error
                manager.disconnect()
                raise HTTPException(status_code=500, detail=f"Failed to start remote training: {exc}")

            # Record job metadata
            _record_job(model_id, {
                "mode": "remote",
                "remote_job_id": job_id,
                "role": request.role,
                "epochs": request.epochs,
                "batch_size": request.batch_size,
                "status": "running",
                "started_at": datetime.utcnow().isoformat() + "Z"
            })

            return TrainingResponse(status="started", model_id=model_id,
                                    message=f"Remote training started with job ID {job_id}")

        # Handle local training
        else:
            # Validate that fine‑tuning functionality is available
            if start_fine_tuning is None:
                raise HTTPException(status_code=503, detail="Local fine‑tuning is unavailable in this environment")

            def run_local():
                """Inner function to execute fine‑tuning in the background."""
                try:
                    # Start fine‑tuning and store output path
                    model_path = start_fine_tuning(
                        model_id=model_id,
                        role_file=str(role_file_path),
                        batch_size=request.batch_size,
                        epochs=request.epochs,
                        use_lora=request.use_lora
                    )
                    # Record completion
                    training_jobs[model_id]["status"] = "completed"
                    training_jobs[model_id]["model_path"] = model_path
                except Exception as exc:
                    training_jobs[model_id]["status"] = "failed"
                    training_jobs[model_id]["error"] = str(exc)

            # Record job metadata
            _record_job(model_id, {
                "mode": "local",
                "role": request.role,
                "epochs": request.epochs,
                "batch_size": request.batch_size,
                "status": "pending",
                "started_at": datetime.utcnow().isoformat() + "Z"
            })

            # Schedule background task
            background_tasks.add_task(run_local)

            return TrainingResponse(status="started", model_id=model_id,
                                    message="Local training started")

    @app.get("/status/{model_id}", response_model=StatusResponse)
    async def get_status(model_id: str):
        """Retrieve the status of a training job.

        Returns current status, progress information, and any error details.
        """
        job = training_jobs.get(model_id)
        if not job:
            raise HTTPException(status_code=404, detail="Model ID not found")

        # Remote jobs: query remote status
        if job.get("mode") == "remote":
            if get_ssh_manager is None or TrainingConfig is None:
                raise HTTPException(status_code=503, detail="Remote training is unavailable in this environment")
            manager = get_ssh_manager()
            if not manager:
                raise HTTPException(status_code=503, detail="SSH manager is not configured")
            remote_job_id = job.get("remote_job_id")
            try:
                status_info = manager.check_training_status(remote_job_id)
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Failed to get remote status: {exc}")
            return StatusResponse(status=status_info.get("status"),
                                  progress=status_info.get("latest_log"))

        # Local jobs: return recorded status
        return StatusResponse(status=job.get("status"),
                              progress=None)

    @app.get("/download/{model_id}", response_model=DownloadResponse)
    async def download(model_id: str):
        """Provide a download link for a completed model.

        For local training, the model is served via upload_model/storage backend.
        For remote training, the model is downloaded from the remote server and then served.
        """
        job = training_jobs.get(model_id)
        if not job:
            raise HTTPException(status_code=404, detail="Model ID not found")

        # Remote models: fetch from remote server
        if job.get("mode") == "remote":
            if get_ssh_manager is None or TrainingConfig is None:
                raise HTTPException(status_code=503, detail="Remote training is unavailable in this environment")
            manager = get_ssh_manager()
            if not manager:
                raise HTTPException(status_code=503, detail="SSH manager is not configured")
            remote_job_id = job.get("remote_job_id")

            # Download model to local storage
            local_model_dir = Path("models") / model_id
            try:
                success = manager.download_trained_model(remote_job_id, str(local_model_dir))
                if not success:
                    raise RuntimeError("Download failed")
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Failed to download model: {exc}")

            # Here we could upload to storage backend and return a URL
            # For simplicity, return the path
            return DownloadResponse(status="ready", download_link=str(local_model_dir))

        # Local models: use storage backend if available
        model_path = job.get("model_path")
        if not model_path:
            raise HTTPException(status_code=404, detail="Model not ready yet")

        if upload_model is None:
            # If storage backend not available, just return file path
            return DownloadResponse(status="ready", download_link=model_path)

        try:
            url = upload_model(model_path)
            return DownloadResponse(status="ready", download_link=url)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to provide download link: {exc}")

    @app.get("/ssh/status", response_model=SSHStatusResponse)
    async def ssh_status():
        """Check the status of the SSH connection.

        Returns whether a remote SSH server is reachable using the configured
        parameters. This endpoint attempts to establish and immediately close
        a connection to verify connectivity. It does not persist the SSH
        session.
        """
        if get_ssh_manager is None or TrainingConfig is None:
            return SSHStatusResponse(connected=False, error="SSH functionality is unavailable in this environment")
        manager = get_ssh_manager()
        if not manager:
            return SSHStatusResponse(connected=False, error="SSH manager is not configured")
        try:
            ok = manager.connect()
            if ok:
                hostname = getattr(manager.config, "hostname", None)
                # Immediately disconnect to avoid lingering sessions
                manager.disconnect()
                return SSHStatusResponse(connected=True, hostname=hostname)
            else:
                return SSHStatusResponse(connected=False, error="Unable to connect to remote SSH server")
        except Exception as exc:
            return SSHStatusResponse(connected=False, error=str(exc))

    # Additional routes and helper functions would be defined here in a real deployment.
    # In this test environment we avoid defining full route logic to prevent import
    # errors when dependencies like torch or fastapi are missing.

else:
    # When FastAPI is not available, expose no‑op placeholders so that the module can be imported.
    app = None  # type: ignore

    class TrainingRequest:
        """Placeholder for request model when FastAPI/Pydantic is unavailable."""
        pass

    class TrainingResponse:
        """Placeholder for response model when FastAPI/Pydantic is unavailable."""
        pass

    class StatusResponse:
        """Placeholder for status model when FastAPI/Pydantic is unavailable."""
        pass

    class DownloadResponse:
        """Placeholder for download response model when FastAPI/Pydantic is unavailable."""
        pass

    class SSHStatusResponse:
        """Placeholder for SSH status model when FastAPI/Pydantic is unavailable."""
        pass

    # Define dummy functions to avoid NameError in other parts of the code
    def update_progress(model_id: str, progress: Dict) -> None:
        """No‑op progress updater when server functionality is unavailable."""
        return

    async def run_fine_tuning(*args, **kwargs):  # type: ignore
        """Raise runtime error when fine‑tuning is attempted in a stub environment."""
        raise RuntimeError("Fine‑tuning functionality is unavailable in this environment.")

    async def run_remote_fine_tuning(*args, **kwargs):  # type: ignore
        """Raise runtime error when remote fine‑tuning is attempted in a stub environment."""
        raise RuntimeError("Remote fine‑tuning functionality is unavailable in this environment.")