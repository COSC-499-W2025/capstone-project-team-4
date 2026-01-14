from __future__ import annotations
from fastapi import FastAPI, Request, UploadFile, Form, File
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional, List
import os
import shutil
import tempfile
import json
import logging
import traceback
import zipfile
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from src.core import config_manager
from src.main import analyze_project_cli
from src.core.aggregate_outputs import aggregate_outputs, format_markdown, _serialize_projects

BASE = Path(__file__).resolve().parents[2]
OUTPUTS = BASE / "outputs"
TEMPLATES_DIR = BASE / "src" / "webapp" / "templates"
STATIC_DIR = BASE / "src" / "webapp" / "static"

app = FastAPI(title="Mining Digital Work Artifacts - Web UI")

# Static/Template setup
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _list_projects(outputs_dir: Path) -> List[str]:
    if not outputs_dir.exists():
        return []
    return sorted([p.name for p in outputs_dir.iterdir() if p.is_dir()])


def _list_timestamps(project_dir: Path) -> List[str]:
    if not project_dir.exists():
        return []
    return sorted([p.name for p in project_dir.iterdir() if p.is_dir()])


def _restore_zip_timestamps(extract_path: Path, zip_path: Path):
    """
    Restore original file timestamps from ZIP metadata after extraction.
    
    Args:
        extract_path: Directory where files were extracted
        zip_path: Path to the source ZIP file
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for info in zf.infolist():
                # Get the date_time tuple (year, month, day, hour, minute, second)
                date_time = info.date_time
                # Convert to timestamp
                dt = datetime(*date_time)
                timestamp = dt.timestamp()
                
                # Get the extracted file path
                file_path = extract_path / info.filename
                
                # Only process files that exist and are not directories
                if file_path.exists() and not file_path.is_dir():
                    try:
                        # Set the file's access and modification times
                        os.utime(file_path, (timestamp, timestamp))
                        logger.debug(f"Restored timestamp for {info.filename}: {dt}")
                    except Exception as e:
                        logger.warning(f"Could not restore timestamp for {info.filename}: {e}")
    except Exception as e:
        logger.warning(f"Could not restore ZIP timestamps: {e}")



@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    try:
        logger.info("GET / - Home page request")
        projects = _list_projects(OUTPUTS)
        logger.info(f"Found {len(projects)} projects")
        consent_cfg = config_manager.read_cfg()
        
        # Aggregate all project outputs for chronological display
        aggregated_projects = aggregate_outputs(OUTPUTS)
        logger.info(f"Aggregated {len(aggregated_projects)} project records")
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "projects": projects,
                "cfg": consent_cfg,
                "aggregated": aggregated_projects,
            },
        )
    except Exception as e:
        logger.error(f"Error rendering home page: {e}", exc_info=True)
        return HTMLResponse(f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


@app.post("/analyze")
async def analyze(
    path_text: Optional[str] = Form(None),
    include_files: Optional[bool] = Form(True),
    out_dir: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    logger.info(f"POST /analyze - path_text={path_text}, include_files={include_files}, out_dir={out_dir}, file={file.filename if file else None}")
    try:
        config_manager.require_consent()
        logger.info("Consent verified")
    except SystemExit as e:
        logger.error(f"Consent not granted: {e}")
        return JSONResponse({"error": "Consent required"}, status_code=400)

    out = Path(out_dir).resolve() if out_dir else OUTPUTS
    out.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {out}")

    # Determine input source
    tmp_zip_path: Optional[Path] = None
    tmp_dir: Optional[Path] = None
    input_path: Optional[Path] = None
    
    if file is not None and file.filename:
        logger.info(f"Processing uploaded file: {file.filename}")
        # Preserve original filename so project_name matches the uploaded ZIP name
        tmp_dir = Path(tempfile.mkdtemp())
        target_name = Path(file.filename).name
        tmp_zip_path = tmp_dir / target_name
        with tmp_zip_path.open("wb") as tmp:
            shutil.copyfileobj(file.file, tmp)
        logger.info(f"Uploaded file saved to temp: {tmp_zip_path}")
        input_path = tmp_zip_path
            
    elif path_text:
        input_path = Path(path_text).expanduser().resolve()
        logger.info(f"Using path: {input_path}")
    else:
        logger.error("No path or file provided")
        return JSONResponse({"error": "Provide either a path or upload a file"}, status_code=400)

    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        if tmp_zip_path and tmp_zip_path.exists():
            tmp_zip_path.unlink(missing_ok=True)
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        return JSONResponse({"error": f"Path not found: {input_path}"}, status_code=400)

    # Run CLI function, then discover latest timestamp dir for feedback
    try:
        logger.info(f"Starting analysis on {input_path}")
        analyze_project_cli(path=input_path, include_files=include_files, out=out)
        logger.info(f"Analysis completed successfully")
        
        # If this was a ZIP file, restore timestamps in the output directory
        if tmp_zip_path and tmp_zip_path.exists():
            project_name = input_path.stem if input_path else "project"
            project_root = out / project_name
            if project_root.exists():
                ts_list = _list_timestamps(project_root)
                if ts_list:
                    latest_ts = ts_list[-1]
                    run_dir = project_root / latest_ts
                    logger.info(f"Restoring ZIP file timestamps for {project_name}/{latest_ts}")
                    _restore_zip_timestamps(run_dir, tmp_zip_path)
    except SystemExit as e:
        logger.error(f"Analysis failed with SystemExit: {e}")
        if tmp_zip_path and tmp_zip_path.exists():
            tmp_zip_path.unlink(missing_ok=True)
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
        if tmp_zip_path and tmp_zip_path.exists():
            tmp_zip_path.unlink(missing_ok=True)
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        # Clean up temporary files/directories after analysis
        if tmp_zip_path and tmp_zip_path.exists():
            logger.info(f"Cleaning up temp ZIP file: {tmp_zip_path}")
            tmp_zip_path.unlink(missing_ok=True)
        if tmp_dir:
            logger.info(f"Cleaning up temp directory: {tmp_dir}")
            shutil.rmtree(tmp_dir, ignore_errors=True)

    # Find latest run folder for this project name
    project_name = input_path.stem if input_path else "project"
    project_root = out / project_name
    latest = None
    if project_root.exists():
        ts_list = _list_timestamps(project_root)
        latest = ts_list[-1] if ts_list else None
        logger.info(f"Found {len(ts_list)} timestamps, latest: {latest}")
    else:
        logger.warning(f"Project root not found: {project_root}")

    redirect_url = f"/project/{project_name}?ts={latest or ''}"
    logger.info(f"Redirecting to {redirect_url}")
    return RedirectResponse(url=redirect_url, status_code=303)


@app.get("/project/{project_name}", response_class=HTMLResponse)
async def project_view(request: Request, project_name: str, ts: Optional[str] = None):
    try:
        logger.info(f"GET /project/{project_name} - ts={ts}")
        project_dir = OUTPUTS / project_name
        timestamps = _list_timestamps(project_dir)
        selected_ts = ts or (timestamps[-1] if timestamps else None)
        files = []
        if selected_ts:
            run_dir = project_dir / selected_ts
            files = [p.name for p in run_dir.glob("*.json")]
            logger.info(f"Found {len(files)} JSON files in {run_dir}")
        logger.info(f"Rendering project {project_name} with {len(timestamps)} timestamps")
        return templates.TemplateResponse(
            "project.html",
            {
                "request": request,
                "project": project_name,
                "timestamps": timestamps,
                "selected_ts": selected_ts,
                "files": files,
            },
        )
    except Exception as e:
        logger.error(f"Error rendering project view: {e}", exc_info=True)
        return HTMLResponse(f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


# @app.get("/project/{project_name}/{ts}/{filename}")
# async def view_json(project_name: str, ts: str, filename: str):
#     try:
#         logger.info(f"GET /project/{project_name}/{ts}/{filename}")
#         target = OUTPUTS / project_name / ts / filename
#         if not target.exists():
#             logger.warning(f"File not found: {target}")
#             return JSONResponse({"error": "Not found"}, status_code=404)
#         try:
#             data = json.loads(target.read_text(encoding="utf-8"))
#             logger.info(f"Loaded JSON file: {target}")
#             return JSONResponse(data)
#         except Exception as e:
#             logger.debug(f"Not JSON, returning as plaintext: {e}")
#             return PlainTextResponse(target.read_text(encoding="utf-8"))
#     except Exception as e:
#         logger.error(f"Error viewing file: {e}", exc_info=True)
#         return JSONResponse({"error": str(e)}, status_code=500)


# @app.post("/delete")
# async def delete_run(project: str = Form(...), ts: str = Form(...)):
#     try:
#         logger.info(f"POST /delete - project={project}, ts={ts}")
#         run_dir = OUTPUTS / project / ts
#         if not run_dir.exists():
#             logger.warning(f"Run directory not found: {run_dir}")
#             return JSONResponse({"error": "Run not found"}, status_code=404)
#         logger.info(f"Deleting directory: {run_dir}")
#         shutil.rmtree(run_dir)
#         logger.info(f"Successfully deleted: {run_dir}")
#         return RedirectResponse(url=f"/project/{project}", status_code=303)
#     except Exception as e:
#         logger.error(f"Error deleting run: {e}", exc_info=True)
#         return JSONResponse({"error": str(e)}, status_code=500)


# @app.get("/aggregate")
# async def aggregate(json_output: bool = False):
#     logger.info(f"GET /aggregate - json_output={json_output}")
#     try:
#         projects = aggregate_outputs(OUTPUTS)
#         logger.info(f"Aggregated {len(projects)} projects")
#         if json_output:
#             serial = _serialize_projects(projects)
#             logger.info("Returning JSON format")
#             return JSONResponse(serial)
#         content = format_markdown(projects)
#         logger.info("Returning Markdown format")
#         return PlainTextResponse(content)
#     except Exception as e:
#         logger.error(f"Error aggregating outputs: {e}", exc_info=True)
#         return JSONResponse({"error": str(e)}, status_code=500)


# Health check
@app.get("/health")
async def health():
    logger.debug("Health check requested")
    return {"status": "ok"}
