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


# OLD CODE: No longer needed - metadata is now saved before analysis
# def _restore_zip_timestamps(extract_path: Path, zip_path: Path):
#     """
#     Extract the earliest file timestamp from ZIP and save as project start date.
#     This ensures metadata_parser can access the original project date.
#     
#     Args:
#         extract_path: Directory where files were extracted
#         zip_path: Path to the source ZIP file
#     """
#     try:
#         # Get earliest timestamp from files in the ZIP
#         earliest_timestamp = None
#         earliest_dt = None
#         
#         with zipfile.ZipFile(zip_path, 'r') as zf:
#             for info in zf.infolist():
#                 if info.is_dir():
#                     continue
#                 # Get the date_time tuple (year, month, day, hour, minute, second)
#                 date_time = info.date_time
#                 dt = datetime(*date_time)
#                 timestamp = dt.timestamp()
#                 
#                 if earliest_timestamp is None or timestamp < earliest_timestamp:
#                     earliest_timestamp = timestamp
#                     earliest_dt = dt
#         
#         # Save the ZIP start date for metadata_parser to use
#         if earliest_timestamp is not None:
#             zip_start_date_file = extract_path / ".zip_started_date.json"
#             start_date_data = {
#                 "timestamp": earliest_timestamp,
#                 "date_time": earliest_dt.isoformat(),
#                 "date_time_str": str(earliest_dt)
#             }
#             try:
#                 with open(zip_start_date_file, 'w') as f:
#                     json.dump(start_date_data, f, indent=2)
#                 logger.info(f"Saved ZIP start date ({earliest_dt}) to {zip_start_date_file}")
#             except Exception as e:
#                 logger.warning(f"Could not save ZIP start date: {e}")
#         else:
#             logger.warning("No files found in ZIP to determine start date")
#             
#     except Exception as e:
#         logger.warning(f"Could not process ZIP timestamps: {e}")




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
    tmp_zip_metadata: Optional[Dict[str, Any]] = None
    extracted_zip_dir: Optional[Path] = None
    
    if file is not None and file.filename:
        logger.info(f"Processing uploaded file: {file.filename}")
        # Preserve original filename so project_name matches the uploaded ZIP name
        tmp_dir = Path(tempfile.mkdtemp())
        target_name = Path(file.filename).name
        tmp_zip_path = tmp_dir / target_name
        with tmp_zip_path.open("wb") as tmp:
            shutil.copyfileobj(file.file, tmp)
        logger.info(f"Uploaded file saved to temp: {tmp_zip_path}")
        
        # Extract ZIP metadata BEFORE analysis
        # IMPORTANT: Files within ZIP archives preserve their original creation timestamps.
        # metadata_parser.py uses these timestamps to set file timestamps in extracted files.
        # We must extract and preserve this metadata for later use in metadata_parser.
        try:
            earliest_timestamp = None
            earliest_dt = None
            with zipfile.ZipFile(tmp_zip_path, 'r') as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    dt = datetime(*info.date_time)
                    timestamp = dt.timestamp()
                    if earliest_timestamp is None or timestamp < earliest_timestamp:
                        earliest_timestamp = timestamp
                        earliest_dt = dt
            
            if earliest_dt:
                tmp_zip_metadata = {
                    "timestamp": earliest_timestamp,
                    "date_time": earliest_dt.isoformat(),
                    "date_time_str": str(earliest_dt)
                }
                logger.info(f"Extracted ZIP metadata: {tmp_zip_metadata}")
        except Exception as e:
            logger.warning(f"Could not extract ZIP metadata: {e}")
        
        # Extract ZIP to a persistent directory so metadata_parser can read .zip_started_date.json
        # IMPORTANT: analyze_project_cli() uses TemporaryDirectory internally,
        # which deletes .zip_started_date.json after analysis completes.
        # Therefore, we must pre-extract the ZIP and create the metadata file before analysis.
        try:
            extracted_zip_dir = Path(tempfile.mkdtemp())
            logger.info(f"Extracting ZIP to {extracted_zip_dir}")
            with zipfile.ZipFile(tmp_zip_path, 'r') as zf:
                zf.extractall(extracted_zip_dir)
            
            # Find the actual project directory (first non-hidden directory)
            # ZIPs typically contain a project-name/ subdirectory.
            # We exclude __MACOSX/ as it's automatically generated by macOS.
            # NOTE: Finding this project directory ensures the output folder is named
            # after the actual project (e.g., capstone-project-team-4) instead of
            # a temporary directory name (e.g., tmpee2r7fm7).
            subdirs = [d for d in extracted_zip_dir.iterdir() if d.is_dir() and not d.name.startswith('.') and d.name != "__MACOSX"]
            
            if subdirs:
                # Use the first subdirectory as the project directory
                project_dir = subdirs[0]
                logger.info(f"Found project directory in ZIP: {project_dir.name}")
                
                # Save ZIP metadata file in the project directory (before analysis)
                # metadata_parser.py reads .zip_started_date.json during analysis
                # and applies the original ZIP creation timestamp to all files.
                if tmp_zip_metadata:
                    zip_start_date_file = project_dir / ".zip_started_date.json"
                    with open(zip_start_date_file, 'w') as f:
                        json.dump(tmp_zip_metadata, f, indent=2)
                    logger.info(f"Pre-created .zip_started_date.json in {project_dir}")
                
                # Use the project directory as input path
                # This ensures the project name is correctly set to "capstone-project-team-4"
                # instead of a temporary directory name.
                input_path = project_dir
            else:
                # Fallback: use extracted directory if no subdirs found
                logger.warning("No subdirectories found in ZIP, using extracted directory")
                if tmp_zip_metadata:
                    zip_start_date_file = extracted_zip_dir / ".zip_started_date.json"
                    with open(zip_start_date_file, 'w') as f:
                        json.dump(tmp_zip_metadata, f, indent=2)
                input_path = extracted_zip_dir
                
        except Exception as e:
            logger.error(f"Could not extract ZIP: {e}")
            return JSONResponse({"error": f"Failed to extract ZIP: {e}"}, status_code=400)
            
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
    original_cwd = Path.cwd()
    try:
        logger.info(f"Starting analysis on {input_path}")
        analyze_project_cli(path=input_path, include_files=include_files)
        logger.info(f"Analysis completed successfully")
        
        # If this was a ZIP file, save the metadata file to the output directory
        if tmp_zip_path and tmp_zip_path.exists() and tmp_zip_metadata:
            project_name = extracted_zip_dir.name if extracted_zip_dir else input_path.stem
            project_root = out / project_name
            if project_root.exists():
                ts_list = _list_timestamps(project_root)
                if ts_list:
                    latest_ts = ts_list[-1]
                    run_dir = project_root / latest_ts
                    # Verify and copy ZIP metadata to final output directory
                    zip_start_date_file = run_dir / ".zip_started_date.json"
                    if not zip_start_date_file.exists():
                        try:
                            with open(zip_start_date_file, 'w') as f:
                                json.dump(tmp_zip_metadata, f, indent=2)
                            logger.info(f"Confirmed ZIP start date in {zip_start_date_file}")
                        except Exception as e:
                            logger.warning(f"Could not save ZIP start date: {e}")
                    logger.info(f"ZIP metadata saved for {project_name}/{latest_ts}")
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
    # Find latest run folder for this project name (BEFORE cleanup)
    # For extracted ZIPs, input_path is the actual project directory
    # IMPORTANT: The following logic executes before extracted_zip_dir is deleted.
    # This ensures the project name is set to the actual name (e.g., capstone-project-team-4)
    # instead of a temporary directory name (e.g., tmpee2r7fm7).
    if extracted_zip_dir:
        # Project name is from the input_path (which is the subdirectory we found)
        project_name = input_path.name
        logger.info(f"Using project name from extracted ZIP: {project_name}")
    else:
        project_name = input_path.stem if input_path else "project"
        logger.info(f"Using project name from direct path: {project_name}")
    
    # Now cleanup
    os.chdir(original_cwd)
    
    # Clean up temporary files/directories after analysis
    if tmp_zip_path and tmp_zip_path.exists():
        logger.info(f"Cleaning up temp ZIP file: {tmp_zip_path}")
        tmp_zip_path.unlink(missing_ok=True)
    if tmp_dir:
        logger.info(f"Cleaning up temp directory: {tmp_dir}")
        shutil.rmtree(tmp_dir, ignore_errors=True)
    if extracted_zip_dir and extracted_zip_dir.exists():
        logger.info(f"Cleaning up extracted ZIP directory: {extracted_zip_dir}")
        shutil.rmtree(extracted_zip_dir, ignore_errors=True)
    # Find latest run folder for this project name
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



# Health check
@app.get("/health")
async def health():
    logger.debug("Health check requested")
    return {"status": "ok"}


