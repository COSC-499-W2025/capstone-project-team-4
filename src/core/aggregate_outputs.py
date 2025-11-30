from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
import sys

def try_load_json(p: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def parse_date_str(s: str) -> Optional[datetime]:
    if not s:
        return None
    s = s.strip()
    # try ISO
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass
    # try common timestamp folder format YYYY-MM-DD_HH-MM-SS or YYYY-MM-DD
    for fmt in ("%Y-%m-%d_%H-%M-%S", "%Y-%m-%d", "%Y-%m"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    # try first 10 chars as YYYY-MM-DD
    try:
        return datetime.fromisoformat(s[:10])
    except Exception:
        return None

def infer_complexity_level(complexity_json: Dict[str, Any]) -> str:
    funcs = complexity_json.get("functions") if isinstance(complexity_json, dict) else None
    if not funcs or not isinstance(funcs, list):
        return "Unknown"
    nums = []
    for f in funcs:
        try:
            val = float(f.get("cyclomatic", 0) or 0)
            nums.append(val)
        except Exception:
            pass
    if not nums:
        return "Unknown"
    avg = sum(nums) / len(nums)
    if avg >= 10:
        return "High"
    if avg >= 5:
        return "Medium"
    return "Low"

def extract_record(project_dir: Path, ts_dir: Path) -> Dict[str, Any]:
    rec = {"name": project_dir.name, "started": None, "languages": [], "frameworks": [], "skills": [], "loc": None, "files": None, "complexity": None, "key_features": [], "ts_dir_date": None}
    skill_path = ts_dir / "skill_extract.json"
    meta_path = ts_dir / "metadata.json"
    complexity_path = ts_dir / "complexity.json"
    stats_path = ts_dir / "stats_summary.json"
    tech_path = ts_dir / "technologies.json"

    # skill_extract first
    skill = try_load_json(skill_path) or {}
    rec["languages"] = skill.get("languages") or skill.get("detected_languages") or []
    rec["frameworks"] = skill.get("frameworks") or skill.get("detected_frameworks") or []
    rec["skills"] = skill.get("skills") or skill.get("skills_flat") or []
    if not rec["skills"]:
        cats = skill.get("skill_categories") or skill
        if isinstance(cats, dict):
            allsk = []
            for v in cats.values():
                if isinstance(v, list):
                    allsk.extend(v)
            rec["skills"] = sorted(set(allsk))

    # started date from skill or metadata
    started = skill.get("started") or skill.get("date") or skill.get("timestamp")
    if started:
        dt = parse_date_str(started)
        if dt:
            rec["started"] = dt

    # technologies.json fallback
    tech = try_load_json(tech_path) or {}
    if not rec["languages"]:
        rec["languages"] = tech.get("languages") or []
    if not rec["frameworks"]:
        rec["frameworks"] = tech.get("frameworks") or []

    # metadata: files count
    meta = try_load_json(meta_path) or {}
    files = meta.get("files")
    if isinstance(files, list):
        rec["files"] = len(files)

    # stats_summary for LOC
    stats = try_load_json(stats_path) or {}
    if stats:
        for key in ("total_loc", "loc", "total_lines", "lines"):
            if key in stats:
                try:
                    rec["loc"] = int(stats[key])
                    break
                except Exception:
                    pass

    # complexity
    comp = try_load_json(complexity_path) or {}
    if comp:
        rec["complexity"] = infer_complexity_level(comp)

    # key features: heuristics from skills (pick top 3)
    if rec["skills"]:
        rec["key_features"] = rec["skills"][:3]
    else:
        rec["key_features"] = rec["frameworks"][:3]

    # ts_dir date: parse folder name or use mtime
    dt = parse_date_str(ts_dir.name)
    if not dt:
        try:
            dt = datetime.fromtimestamp(ts_dir.stat().st_mtime)
        except Exception:
            dt = None
    rec["ts_dir_date"] = dt

    # fallback for started: parse timestamp folder name or project_dir mtime
    if not rec["started"]:
        if dt:
            rec["started"] = dt
    if not rec["started"]:
        try:
            rec["started"] = datetime.fromtimestamp(project_dir.stat().st_mtime)
        except Exception:
            rec["started"] = datetime.now()

    return rec

def aggregate_outputs(outputs_root: Path) -> List[Dict[str, Any]]:
    projects = []
    if not outputs_root.exists():
        print("outputs path not found:", outputs_root, file=sys.stderr)
        return []
    for proj_dir in sorted([p for p in outputs_root.iterdir() if p.is_dir()]):
        ts_dirs = [d for d in proj_dir.iterdir() if d.is_dir()]
        if not ts_dirs:
            continue
        records = [extract_record(proj_dir, ts) for ts in ts_dirs]
        if not records:
            continue
        # earliest started among records
        records_with_started = [r for r in records if r.get("started")]
        records_with_started.sort(key=lambda r: r["started"])
        earliest = records_with_started[0] if records_with_started else records[0]
        # last updated is max ts_dir_date among records (fallback to latest started)
        ts_dates = [r["ts_dir_date"] for r in records if r.get("ts_dir_date")]
        last_updated = max(ts_dates) if ts_dates else (earliest.get("started") or datetime.now())

        # normalize lists
        earliest["languages"] = sorted(set(earliest.get("languages") or []))
        earliest["frameworks"] = sorted(set(earliest.get("frameworks") or []))
        earliest["skills"] = sorted(set(earliest.get("skills") or []))

        # attach last_updated
        earliest["last_updated"] = last_updated

        projects.append(earliest)
    # sort by last_updated descending so newest appear first
    projects.sort(key=lambda p: p.get("last_updated") or datetime.min, reverse=True)
    return projects

def format_markdown(projects: List[Dict[str, Any]]) -> str:
    lines = []
    for p in projects:
        last = p.get("last_updated")
        last_str = last.strftime("%Y-%m-%d") if last else "Unknown"
        lines.append(f"{last_str} (Last updated)")
        lines.append(f"→ {p['name']}")
        started = p.get("started")
        if started:
            lines.append(f"   - Started: {started.strftime('%Y-%m-%d')}")
        tech = []
        if p.get("frameworks"):
            tech.extend(p["frameworks"])
        if p.get("languages"):
            tech.extend([l for l in p["languages"] if l not in tech])
        if tech:
            lines.append(f"   - Tech: {', '.join(tech)}")
        loc = f"{p['loc']:,}" if isinstance(p.get("loc"), int) else ("Unknown" if p.get("loc") is None else str(p.get("loc")))
        files = str(p["files"]) if p.get("files") is not None else "Unknown"
        lines.append(f"   - LOC: {loc} / Files: {files}")
        if p.get("complexity"):
            lines.append(f"   - Complexity: {p['complexity']}")
        if p.get("key_features"):
            lines.append(f"   - Key Features: {', '.join(p['key_features'])}")
        lines.append("")  # blank line
    return "\n".join(lines)

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("outputs", nargs="?", default="outputs", help="Path to outputs root")
    ap.add_argument("--out", "-o", help="Write markdown to file")
    args = ap.parse_args()

    out_root = Path(args.outputs)
    projects = aggregate_outputs(out_root)
    md = format_markdown(projects)
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        print("Wrote:", args.out)
    else:
        print(md)

if __name__ == "__main__":
    main()