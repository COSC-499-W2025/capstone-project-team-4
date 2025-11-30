from __future__ import annotations
import os
import json
from collections import defaultdict
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from git import Repo, InvalidGitRepositoryError
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from .code_complexity_analyzer import (
    FunctionMetrics,
    analyze_file,
    EXT_TO_LANG,
)


# Git/Collaboration Analysis Functions
@lru_cache(maxsize=1024)  # Cache email processing results
def _extract_base_email(email: str) -> str:
    """Extract the base email from GitHub noreply formats."""
    email = email.lower().strip()
    if '@users.noreply.github.com' in email:
        noreply_part = email.split('@users.noreply.github.com')[0]
        if '+' in noreply_part:
            # Format: "12345+actual@email.com@users.noreply.github.com"
            base_part = noreply_part.split('+', 1)[1]
            if '@' in base_part:
                return base_part  # Return the actual email
        # Return the noreply format as-is if no actual email found
    return email


@lru_cache(maxsize=512)  # Cache username extraction results
def _extract_username(name: str, emails_tuple: Tuple[str, ...]) -> str:
    """Extract a reasonable username from name and email information."""
    # Priority order: GitHub username from noreply email, email username, cleaned name
    
    # Convert tuple back to list for processing (needed for caching)
    emails = list(emails_tuple)
    
    # Try to extract GitHub username from noreply emails
    for email in emails:
        if '@users.noreply.github.com' in email.lower():
            noreply_part = email.split('@users.noreply.github.com')[0]
            if '+' in noreply_part:
                # Format: "12345+username@users.noreply.github.com"
                potential_username = noreply_part.split('+', 1)[1]
                if '@' not in potential_username and potential_username.strip():
                    return potential_username.strip()
            else:
                # Format: "username@users.noreply.github.com"
                if noreply_part.strip() and not noreply_part.isdigit():
                    return noreply_part.strip()
    
    # Try to extract username from regular email addresses
    for email in emails:
        if '@' in email and '@users.noreply.github.com' not in email.lower():
            username_part = email.split('@')[0]
            if username_part.strip():
                return username_part.strip()
    
    # Fall back to cleaned name (remove spaces, convert to lowercase)
    if name:
        cleaned_name = name.lower().replace(' ', '').replace('-', '').replace('_', '')
        if cleaned_name:
            return cleaned_name
    
    # Final fallback
    return "unknown"


@lru_cache(maxsize=256)  # Cache merge decisions
def _should_merge_contributors_cached(name1: str, name2: str, emails1_tuple: Tuple[str, ...], emails2_tuple: Tuple[str, ...]) -> bool:
    """Cached version of contributor merge detection."""
    emails1 = set(emails1_tuple)
    emails2 = set(emails2_tuple)
    
    # Quick check: if any emails match exactly, merge
    if emails1.intersection(emails2):
        return True
    
    # Extract base emails for comparison
    base_emails1 = {_extract_base_email(e) for e in emails1}
    base_emails2 = {_extract_base_email(e) for e in emails2}
    
    # Quick base email intersection check
    if base_emails1.intersection(base_emails2):
        return True
        
    return _detailed_merge_check(name1, name2, emails1, emails2, base_emails1, base_emails2)

def _detailed_merge_check(name1: str, name2: str, emails1: Set[str], emails2: Set[str], base_emails1: Set[str], base_emails2: Set[str]) -> bool:
    """Detailed merge checking logic separated for performance."""
    # Rule 1: Exact same real email address (non-noreply)
    real_emails1 = {e for e in base_emails1 if '@users.noreply.github.com' not in e}
    real_emails2 = {e for e in base_emails2 if '@users.noreply.github.com' not in e}
    
    if real_emails1 and real_emails2 and real_emails1.intersection(real_emails2):
        return True
    
    # Rule 2: Extract embedded real emails from GitHub noreply formats
    embedded_emails1 = set()
    embedded_emails2 = set()
    
    for email in emails1:
        if '@users.noreply.github.com' in email and '+' in email:
            noreply_part = email.split('@users.noreply.github.com')[0]
            if '+' in noreply_part:
                potential_email = noreply_part.split('+', 1)[1]
                if '@' in potential_email and '.' in potential_email:
                    embedded_emails1.add(potential_email)
    
    for email in emails2:
        if '@users.noreply.github.com' in email and '+' in email:
            noreply_part = email.split('@users.noreply.github.com')[0]
            if '+' in noreply_part:
                potential_email = noreply_part.split('+', 1)[1]
                if '@' in potential_email and '.' in potential_email:
                    embedded_emails2.add(potential_email)
    
    # Check if embedded emails match real emails
    if embedded_emails1.intersection(real_emails2) or embedded_emails2.intersection(real_emails1):
        return True
    
    if embedded_emails1.intersection(embedded_emails2):
        return True
    
    # Rule 3: Same real email with different names (variations)
    if real_emails1.intersection(real_emails2):
        return True
    
    # Rule 4: Name similarity analysis
    # Remove common variations and check similarity
    clean_name1 = name1.replace('-', '').replace('_', '').replace(' ', '').replace('.', '')
    clean_name2 = name2.replace('-', '').replace('_', '').replace(' ', '').replace('.', '')
    
    # Check if one name contains the other
    if len(clean_name1) >= 3 and len(clean_name2) >= 3:
        if clean_name1 in clean_name2 or clean_name2 in clean_name1:
            # Additional check: ensure this isn't a false positive
            # If names are very different lengths, require additional evidence
            length_ratio = max(len(clean_name1), len(clean_name2)) / min(len(clean_name1), len(clean_name2))
            if length_ratio <= 2.0:  # Names are reasonably similar in length
                return True
    
    # Rule 5: Check for common GitHub username patterns
    # Extract potential usernames from both names and emails
    usernames1 = {name1.replace(' ', '').replace('-', '').lower()}
    usernames2 = {name2.replace(' ', '').replace('-', '').lower()}
    
    # Add variations from email usernames
    for email in emails1:
        if '@' in email:
            username = email.split('@')[0].lower()
            usernames1.add(username.replace('.', '').replace('_', '').replace('-', ''))
            # For noreply emails, extract the actual username part
            if '@users.noreply.github.com' in email:
                if '+' in username:
                    actual_username = username.split('+')[1] if not username.split('+')[1].isdigit() else None
                    if actual_username:
                        usernames1.add(actual_username.replace('.', '').replace('_', '').replace('-', ''))
    
    for email in emails2:
        if '@' in email:
            username = email.split('@')[0].lower()
            usernames2.add(username.replace('.', '').replace('_', '').replace('-', ''))
            # For noreply emails, extract the actual username part
            if '@users.noreply.github.com' in email:
                if '+' in username:
                    actual_username = username.split('+')[1] if not username.split('+')[1].isdigit() else None
                    if actual_username:
                        usernames2.add(actual_username.replace('.', '').replace('_', '').replace('-', ''))
    
    # Check for username matches
    if usernames1.intersection(usernames2):
        return True
    
    return False


def _should_merge_contributors(contrib1: dict, contrib2: dict) -> bool:
    """Wrapper function to maintain API compatibility with caching."""
    name1 = contrib1['name'].lower()
    name2 = contrib2['name'].lower() 
    emails1_tuple = tuple(sorted(contrib1['all_emails']))
    emails2_tuple = tuple(sorted(contrib2['all_emails']))
    
    return _should_merge_contributors_cached(name1, name2, emails1_tuple, emails2_tuple)


def _merge_contributors(primary, secondary):
    """
    Merge two contributor records, keeping the primary as base.
    """
    # Combine all stats
    primary['commits'] += secondary['commits']
    primary['total_lines_added'] += secondary['total_lines_added']
    primary['total_lines_deleted'] += secondary['total_lines_deleted']
    
    # Merge history
    primary['history'].extend(secondary['history'])
    
    # Merge file modifications
    for file_path, count in secondary['files_modified'].items():
        primary['files_modified'][file_path] = primary['files_modified'].get(file_path, 0) + count
    
    # Merge email lists and ensure no duplicates
    all_emails_combined = primary.get('all_emails', []) + secondary.get('all_emails', [])
    # Add primary emails if not already in the lists
    all_emails_combined.extend([primary.get('primary_email', ''), secondary.get('primary_email', '')])
    # Remove duplicates and empty strings
    primary['all_emails'] = [email for email in set(all_emails_combined) if email.strip()]
    
    # Use the more complete name (longer is usually better)
    if len(secondary['name']) > len(primary['name']):
        primary['name'] = secondary['name']
    
    return primary


def analyze_contributors(project_path=".", use_all_branches=False, max_commits: Optional[int] = None, include_history=True):
    """
    Analyze commit history for all contributors.
    Groups contributors by normalized identity to avoid duplicates (noreply vs real email, name variations).
    If use_all_branches=True then use '--all', otherwise just analyze the current branch

    Includes:
        - total commits
        - percent of total commits
        - commit history (optional for performance)
        - lines added / deleted
        - files modified
        
    Args:
        project_path: Path to git repository
        use_all_branches: Whether to analyze all branches
        max_commits: Maximum commits to process (None for all)
        include_history: Whether to include detailed commit history (memory intensive)
    """
    start_time = time.time()
    print(f"⚡ Starting optimized contributor analysis for: {project_path}")
    print(f"🌳 Branch scope: {'All branches' if use_all_branches else 'Current branch only'}")
    if max_commits:
        print(f"🔢 Max commits limit: {max_commits:,}")
    print(f"📝 Include history: {'Yes' if include_history else 'No (performance mode)'}")

    try:
        repo = Repo(project_path)
        print(f"✅ Git repository found and loaded")
    except InvalidGitRepositoryError:
        print(
            f"❌ [WARN] No .git directory found at {project_path}. Returning empty contributors."
        )
        return []

    contributors = {}
    commit_counts = defaultdict(int)
    contributor_emails = defaultdict(set)  # Track all emails per contributor
    total_commits_processed = 0
    bots_skipped = 0
    
    # Pre-compile bot detection pattern for performance
    bot_indicators = {"[bot]", "bot@", "noreply@github.com", "dependabot"}

    # NOTE: By default, it will get the commits from only the current branch HEAD. If you want to get all commits,
    # input -all instead. So it would be, `repo.iter_commits('--all')`
    print(f"🔍 Starting optimized commit history analysis...")

    commit_range = "--all" if use_all_branches else None
    
    # Batch processing for better performance
    batch_size = 100
    commits_batch = []

    try:
        commit_range = "--all" if use_all_branches else None
        commit_iter = repo.iter_commits(commit_range)
        
        # Apply max_commits limit if specified
        if max_commits:
            from itertools import islice
            commit_iter = islice(commit_iter, max_commits)
            
        for commit in commit_iter:
            total_commits_processed += 1
            
            # Progress reporting every 100 commits (reduced frequency)
            if total_commits_processed % 100 == 0:
                elapsed = time.time() - start_time
                rate = total_commits_processed / elapsed
                print(f"  ⚡ Processed {total_commits_processed:,} commits ({rate:.1f}/sec), found {len(contributors)} unique contributors")
                
            # Early exit if max_commits reached
            if max_commits and total_commits_processed >= max_commits:
                print(f"  🔢 Reached max commits limit: {max_commits:,}")
                break

            raw_name = commit.author.name.strip()
            raw_email = commit.author.email.strip().lower()

            # Optimized bot detection
            if any(indicator in raw_name.lower() or indicator in raw_email for indicator in bot_indicators):
                bots_skipped += 1
                continue

            # Use name+email as initial unique key (we'll deduplicate later)
            identity_key = f"{raw_name}|{raw_email}"

            # Initialize contributor record
            if identity_key not in contributors:
                print(f"  👤 New contributor discovered: {raw_name} ({raw_email})")
                contributors[identity_key] = {
                    "name": raw_name,
                    "primary_email": raw_email,
                    "all_emails": [raw_email],
                    "commits": 0,
                    "percent": 0,
                    "history": [],
                    "total_lines_added": 0,
                    "total_lines_deleted": 0,
                    "files_modified": defaultdict(int),
                }
                contributor_emails[identity_key] = set([raw_email])

            commit_counts[identity_key] += 1

            try:
                stats = commit.stats
                # Per-file modifications
                for file_path, file_stats in stats.files.items():
                    contributors[identity_key]["files_modified"][file_path] += 1

                # Line-level stats
                contributors[identity_key]["total_lines_added"] += stats.total.get(
                    "insertions", 0
                )
                contributors[identity_key]["total_lines_deleted"] += stats.total.get(
                    "deletions", 0
                )

                # Commit history entry (only if requested for memory efficiency)
                if include_history:
                    contributors[identity_key]["history"].append(
                        {
                            "hash": commit.hexsha,
                            "message": commit.message.strip(),
                            "timestamp": commit.committed_date,
                            "files_changed": list(stats.files.keys()),
                            "insertions": stats.total.get("insertions", 0),
                            "deletions": stats.total.get("deletions", 0),
                            "author_name": raw_name,
                            "author_email": raw_email,
                        }
                    )
            except Exception as stats_error:
                print(
                    f"[WARN] Error getting stats for commit {commit.hexsha}: {stats_error}"
                )
                # Add commit without stats
                contributors[identity_key]["history"].append(
                    {
                        "hash": commit.hexsha,
                        "message": commit.message.strip(),
                        "timestamp": commit.committed_date,
                        "files_changed": [],
                        "insertions": 0,
                        "deletions": 0,
                        "author_name": raw_name,
                        "author_email": raw_email,
                    }
                )

    except Exception as e:
        print(
            f"❌ [WARN] Error accessing Git repository commits: {e}. Returning empty contributors."
        )
        return []

    commit_analysis_time = time.time() - start_time
    print(f"✅ Commit analysis complete:")
    print(f"  📊 Total commits processed: {total_commits_processed:,} in {commit_analysis_time:.2f}s")
    print(f"  ⚡ Processing rate: {total_commits_processed/commit_analysis_time:.1f} commits/sec")
    print(f"  🤖 Bot commits skipped: {bots_skipped}")
    print(f"  👥 Initial contributors found: {len(contributors)}")

    # Deduplicate contributors by merging likely duplicates
    print(f"\n🔄 Deduplicating contributors...")
    deduplicated_contributors = {}
    processed_keys = set()
    
    for key1, contrib1 in contributors.items():
        if key1 in processed_keys:
            continue
            
        # Start with this contributor as the base
        merged_contrib = dict(contrib1)
        merged_contrib['all_emails'] = list(contributor_emails[key1])
        merged_commit_count = commit_counts[key1]
        
        # Check against all other contributors for potential merges
        for key2, contrib2 in contributors.items():
            if key1 == key2 or key2 in processed_keys:
                continue
                
            # Prepare contrib2 with all emails for comparison
            contrib2_with_emails = dict(contrib2)
            contrib2_with_emails['all_emails'] = list(contributor_emails[key2])
            
            if _should_merge_contributors(merged_contrib, contrib2_with_emails):
                print(f"  🔗 Merging {contrib2['name']} into {merged_contrib['name']}")
                merged_contrib = _merge_contributors(merged_contrib, contrib2_with_emails)
                merged_commit_count += commit_counts[key2]
                processed_keys.add(key2)
        
        deduplicated_contributors[key1] = merged_contrib
        commit_counts[key1] = merged_commit_count
        processed_keys.add(key1)
    
    print(f"✅ Deduplication complete: {len(contributors)} → {len(deduplicated_contributors)} unique contributors")
    contributors = deduplicated_contributors

    # Format contributors into final list
    total_commits = sum(commit_counts[k] for k in contributors.keys())
    contributor_list = []
    print(f"\n🗜 Processing final contributor statistics...")

    for contributor_key, info in contributors.items():
        commit_count = commit_counts[contributor_key]
        info["commits"] = commit_count

        if total_commits > 0:
            info["percent"] = round((commit_count / total_commits) * 100, 2)
        else:
            info["percent"] = 0

        # Ensure all_emails is properly set and contains all email variations
        if 'all_emails' not in info or not info['all_emails']:
            info["all_emails"] = [info["primary_email"]]
        
        # Remove duplicates and sort emails for consistency
        info["all_emails"] = sorted(list(set(info["all_emails"])))
        
        # Extract username and determine primary email (convert to tuple for caching)
        username = _extract_username(info["name"], tuple(info["all_emails"]))
        
        # Choose primary email (prefer real emails over GitHub noreply)
        real_emails = [e for e in info["all_emails"] if '@users.noreply.github.com' not in e]
        primary_email = real_emails[0] if real_emails else info["all_emails"][0]
        
        # Restructure the output to have name, username, email as primary fields
        contributor_output = {
            "name": info["name"],
            "username": username,
            "email": primary_email,
            "commits": commit_count,
            "percent": info["percent"],
            "total_lines_added": info["total_lines_added"],
            "total_lines_deleted": info["total_lines_deleted"],
            "files_modified": dict(info["files_modified"]),
            "history": info["history"],
            # Additional metadata for debugging/analysis
            "all_emails": info["all_emails"],
            "is_merged_contributor": len(info.get('all_emails', [])) > 1,
            "email_count": len(info.get('all_emails', []))
        }
        
        # Convert defaultdict to normal dict for JSON
        files_touched = len(contributor_output["files_modified"])
        
        # Categorize email types for better understanding
        real_emails = [e for e in info.get('all_emails', []) if '@users.noreply.github.com' not in e]
        github_emails = [e for e in info.get('all_emails', []) if '@users.noreply.github.com' in e]
        contributor_output["real_emails"] = real_emails
        contributor_output["github_noreply_emails"] = github_emails
        
        # Enhanced output showing merged contributor details
        email_count = len(contributor_output['all_emails'])
        email_summary = f"{email_count} email(s)" if email_count > 1 else contributor_output['email']
        print(f"  👤 {contributor_output['name']} (@{contributor_output['username']}): {commit_count} commits ({contributor_output['percent']}%), {files_touched} files touched")
        print(f"    📧 Primary email: {contributor_output['email']}")
        if email_count > 1:
            print(f"       🔗 All emails: {sorted(contributor_output['all_emails'])}")
            # Show which emails are real vs GitHub noreply
            if contributor_output['real_emails']:
                print(f"       ✉️  Real emails: {contributor_output['real_emails']}")
            if contributor_output['github_noreply_emails']:
                print(f"       🐙 GitHub emails: {contributor_output['github_noreply_emails']}")
        print(f"    ➕ Lines: +{contributor_output['total_lines_added']} / -{contributor_output['total_lines_deleted']}")

        contributor_list.append(contributor_output)

    total_time = time.time() - start_time
    print(f"✅ Contributor analysis complete: {len(contributor_list)} contributors processed")
    print(f"⏱️  Total analysis time: {total_time:.2f}s")
    print(f"🚀 Performance: {total_commits_processed/total_time:.1f} commits/sec\n")
    return contributor_list


def calculate_project_stats(project_path, file_list, include_contributors=True, max_commits=None):
    """
    Given the project root (with .git) and the file metadata list,
    compute full project-level statistics.
    
    Args:
        project_path: Path to project root
        file_list: List of file metadata
        include_contributors: Whether to analyze contributors (can be slow)
        max_commits: Maximum commits to process for contributor analysis
    """
    start_time = time.time()
    print(f"⚡ Calculating optimized project statistics...")
    print(f"📂 Project path: {project_path}")
    print(f"📊 File list contains: {len(file_list):,} files")
    if not include_contributors:
        print(f"⚠️  Contributors analysis: DISABLED (performance mode)")
    elif max_commits:
        print(f"📊 Max commits for analysis: {max_commits:,}")

    # File Stats
    print(f"  🗋 Computing file statistics...")
    total_files = len(file_list)
    total_size = sum(
        f.get("file_size", 0) for f in file_list if f.get("file_size") is not None
    )
    avg_size = round(total_size / total_files, 2) if total_files > 0 else 0
    print(f"    • Total files: {total_files}")
    print(f"    • Total size: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
    print(f"    • Average file size: {avg_size:,} bytes")

    # Duration
    print(f"  🕒 Computing project duration...")
    try:
        created_ts = min(
            f["created_timestamp"]
            for f in file_list
            if f["created_timestamp"] is not None
        )
        modified_ts = max(
            f["last_modified"] for f in file_list if f["last_modified"] is not None
        )
        duration_days = round((modified_ts - created_ts) / 86400, 2)
        print(f"    • Project duration: {duration_days} days")
        print(f"    • First file: {created_ts} | Latest: {modified_ts}")
    except ValueError:
        duration_days = 0
        print(f"    ⚠️  Unable to calculate duration (missing timestamps)")

    # Contributors (conditional analysis for performance)
    if include_contributors:
        # For this, we can just analyze the current branch. Set `use_all_branches=True` if all branches need the commit history
        print(f"\n👥 Analyzing project collaboration...")
        contributor_start = time.time()
        contributors = analyze_contributors(
            project_path, 
            use_all_branches=False, 
            max_commits=max_commits,
            include_history=False  # Skip history for performance in stats calculation
        )
        contributor_time = time.time() - contributor_start
        is_collaborative = len(contributors) > 1
        print(f"  🤝 Collaborative project: {'Yes' if is_collaborative else 'No'} ({len(contributors)} contributors in {contributor_time:.2f}s)")
    else:
        contributors = []
        is_collaborative = False
        print(f"\n👥 Skipping collaboration analysis for performance...")

    # Final Metrics
    metrics = {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "average_file_size_bytes": avg_size,
        "duration_days": duration_days,
        "collaborative": is_collaborative,
    }

    total_time = time.time() - start_time
    print(f"\n✅ Project statistics calculation complete!")
    print(f"  🗊 Summary: {total_files:,} files, {duration_days} days, {len(contributors)} contributors")
    print(f"  ⏱️  Total analysis time: {total_time:.2f}s")
    print(f"  🚀 File processing rate: {total_files/total_time:.1f} files/sec\n")
    
    return metrics


def save_project_metrics(metrics: dict, output_filename="project_metrics.json"):
    """
    Save project metrics (from calculate_project_stats) to JSON in root /outputs
    """

    # Navigate to project root and use /outputs directory
    project_root = Path(__file__).resolve().parents[3]  # src/core/analyzer → src/core → src → root
    outputs_dir = project_root / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    output_path = str(outputs_dir / output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Project metrics saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    # For local testing only
    print("[TEST] Running project analyzer...")

    cwd = os.getcwd()
    # By default, the metadata_parser puts the json as: capstone-project-team-4_metadata.json
    test_metadata_path = os.path.join(
        cwd, "outputs/capstone-project-team-4_metadata.json"
    )

    with open(test_metadata_path, "r") as file:
        data = json.load(file)

    file_list = data["files"]
    # This is a fallback if it's missing
    project_path = data.get("project_root", cwd)

    print(f"[INFO] Using project root: {project_path}")

    metrics = calculate_project_stats(project_path, file_list)

    # NOTE: I removed the print statements as now you can just read the generated json file.
    # It clutters the terminal so yeah
    # print("\nPROJECT METRICS")
    # print(json.dumps(metrics, indent=2))

    save_project_metrics(metrics)


# Tree-sitter Analysis Integration
@dataclass
class ProjectAnalysisResult:
    project_root: str
    functions: List[FunctionMetrics]


def _is_ignored(path: Path) -> bool:
    ignored = {".venv", "venv", "__pycache__", ".git", ".pytest_cache"}
    return any(part in ignored for part in path.parts)


def _should_analyze(path: Path) -> bool:
    if not path.is_file():
        return False
    if _is_ignored(path):
        return False
    if path.suffix.lower() not in EXT_TO_LANG:
        return False
    return True


def analyze_project(root: Path, max_workers: int = 4, max_files: Optional[int] = None) -> ProjectAnalysisResult:
    """
    Analyze project code complexity with performance optimizations.
    
    Args:
        root: Path to analyze
        max_workers: Number of parallel workers for file analysis
        max_files: Maximum files to analyze (None for all)
    """
    start_time = time.time()
    print(f"⚡ Starting optimized project code complexity analysis...")
    print(f"📂 Target directory: {root}")
    print(f"👥 Parallel workers: {max_workers}")
    if max_files:
        print(f"📊 Max files limit: {max_files:,}")
    
    root = root.resolve()
    functions: List[FunctionMetrics] = []
    files_processed = 0
    files_skipped = 0

    if root.is_file():
        print(f"📄 Analyzing single file: {root.name}")
        if _should_analyze(root):
            file_functions = analyze_file(root)
            functions.extend(file_functions)
            files_processed += 1
            print(f"  ✅ Found {len(file_functions)} functions")
        else:
            files_skipped += 1
            print(f"  ⚠️  File skipped (not supported or ignored)")
    else:
        print(f"📁 Analyzing directory with parallel processing...")
        
        # Collect all files to analyze first
        files_to_analyze = []
        for path in root.rglob("*"):
            if _should_analyze(path):
                files_to_analyze.append(path)
                if max_files and len(files_to_analyze) >= max_files:
                    print(f"  📊 Reached max files limit: {max_files:,}")
                    break
            else:
                files_skipped += 1
        
        print(f"  📋 Found {len(files_to_analyze)} files to analyze, {files_skipped} skipped")
        
        # Process files in parallel
        if max_workers > 1 and len(files_to_analyze) > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_path = {executor.submit(analyze_file, path): path for path in files_to_analyze}
                
                for future in as_completed(future_to_path):
                    path = future_to_path[future]
                    try:
                        file_functions = future.result()
                        functions.extend(file_functions)
                        files_processed += 1
                        
                        # Progress reporting every 20 files
                        if files_processed % 20 == 0:
                            elapsed = time.time() - start_time
                            rate = files_processed / elapsed
                            print(f"  ⚡ Processed {files_processed}/{len(files_to_analyze)} files ({rate:.1f}/sec), found {len(functions)} functions")
                            
                    except Exception as e:
                        print(f"  ❌ Error analyzing {path}: {e}")
                        files_skipped += 1
        else:
            # Sequential processing for small sets or single worker
            for path in files_to_analyze:
                try:
                    file_functions = analyze_file(path)
                    functions.extend(file_functions)
                    files_processed += 1
                    
                    # Progress reporting every 10 files
                    if files_processed % 10 == 0:
                        elapsed = time.time() - start_time
                        rate = files_processed / elapsed
                        print(f"  📊 Processed {files_processed}/{len(files_to_analyze)} files ({rate:.1f}/sec), found {len(functions)} functions")
                        
                except Exception as e:
                    print(f"  ❌ Error analyzing {path}: {e}")
                    files_skipped += 1

    analysis_time = time.time() - start_time
    print(f"\n✅ Code complexity analysis complete!")
    print(f"  📄 Files processed: {files_processed} in {analysis_time:.2f}s")
    print(f"  ⚡ Processing rate: {files_processed/analysis_time:.1f} files/sec")
    print(f"  ⚠️  Files skipped: {files_skipped}")
    print(f"  🎯 Total functions found: {len(functions)}")
    if functions:
        avg_complexity = sum(f.cyclomatic_complexity for f in functions) / len(functions)
        max_complexity = max(f.cyclomatic_complexity for f in functions)
        print(f"  📈 Average complexity: {avg_complexity:.2f}")
        print(f"  🔥 Maximum complexity: {max_complexity}")
        print(f"  🚀 Function analysis rate: {len(functions)/analysis_time:.1f} functions/sec")
    print(f"")

    return ProjectAnalysisResult(
        project_root=str(root),
        functions=functions,
    )


def project_analysis_to_dict(result: ProjectAnalysisResult) -> dict:
    print(f"🗜 Processing complexity analysis results into structured format...")
    funcs = result.functions
    print(f"  🎯 Processing {len(funcs)} functions from: {result.project_root}")

    total_functions = len(funcs)
    total_complexity = sum(f.cyclomatic_complexity for f in funcs)
    total_lines = sum(f.length_lines for f in funcs)
    
    print(f"  📈 Computing aggregate statistics...")
    print(f"    • Total functions: {total_functions}")
    print(f"    • Total complexity: {total_complexity}")
    print(f"    • Total lines: {total_lines}")

    avg_complexity = total_complexity / total_functions if total_functions else 0.0
    avg_lines = total_lines / total_functions if total_functions else 0.0
    avg_complexity_per_10 = (
        sum(f.complexity_per_10_lines for f in funcs) / total_functions
        if total_functions
        else 0.0
    )
    max_complexity = max((f.cyclomatic_complexity for f in funcs), default=0)
    max_loop_depth = max((f.max_loop_depth for f in funcs), default=0)

    print(f"  🗺 Categorizing functions by complexity levels...")
    buckets = {
        "1-5": 0,
        "6-10": 0,
        "11-20": 0,
        "21+": 0,
    }
    for f in funcs:
        c = f.cyclomatic_complexity
        if c <= 5:
            buckets["1-5"] += 1
        elif c <= 10:
            buckets["6-10"] += 1
        elif c <= 20:
            buckets["11-20"] += 1
        else:
            buckets["21+"] += 1
    
    print(f"    • Complexity distribution: {buckets}")

    print(f"  📁 Computing per-file statistics...")
    per_file: Dict[str, dict] = {}
    for f in funcs:
        pf = per_file.setdefault(
            f.file_path,
            {
                "function_count": 0,
                "total_complexity": 0,
                "max_complexity": 0,
                "total_lines": 0,
            },
        )
        pf["function_count"] += 1
        pf["total_complexity"] += f.cyclomatic_complexity
        pf["total_lines"] += f.length_lines
        pf["max_complexity"] = max(pf["max_complexity"], f.cyclomatic_complexity)
    
    print(f"    • Analyzed {len(per_file)} files with functions")

    for path, stats in per_file.items():
        n = stats["function_count"]
        stats["avg_complexity"] = round(stats["total_complexity"] / n, 2)
        stats["avg_lines"] = round(stats["total_lines"] / n, 2)

    result_dict = {
        "project_root": result.project_root,
        "summary": {
            "total_functions": total_functions,
            "total_lines": total_lines,
            "avg_cyclomatic_complexity": round(avg_complexity, 2),
            "avg_lines_per_function": round(avg_lines, 2),
            "avg_complexity_per_10_lines": round(avg_complexity_per_10, 2),
            "max_complexity": max_complexity,
            "complexity_buckets": buckets,
            "max_loop_depth": max_loop_depth,
        },
        "per_file": per_file,
        "functions": [asdict(f) for f in funcs],
    }
    
    print(f"\n✅ Complexity analysis data structure complete!")
    print(f"  📋 Generated summary with {len(result_dict['functions'])} function records")
    print(f"  📁 Per-file analysis for {len(per_file)} files")
    print(f"  📈 Overall average complexity: {round(avg_complexity, 2)}\n")
    
    return result_dict
