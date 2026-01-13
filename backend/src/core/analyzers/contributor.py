"""
Git contributor analysis module.

Simplified implementation for fast contributor extraction.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

try:
    from git import Repo, InvalidGitRepositoryError
except ImportError:
    Repo = None
    InvalidGitRepositoryError = Exception

logger = logging.getLogger(__name__)

# Maximum commits to analyze (None = unlimited)
MAX_COMMITS = 500


def analyze_contributors(
    project_path: str = ".",
    use_all_branches: bool = False,
    max_commits: Optional[int] = MAX_COMMITS
) -> List[Dict[str, Any]]:
    """
    Analyze Git commit history and extract contributor statistics.

    Args:
        project_path: Path to the Git repository
        use_all_branches: If True, analyze all branches
        max_commits: Maximum commits to process (None = unlimited)

    Returns:
        List of contributor dictionaries with stats
    """
    if Repo is None:
        logger.warning("GitPython not installed")
        return []

    # Open repository
    try:
        repo = Repo(project_path)
    except InvalidGitRepositoryError:
        logger.warning("Not a git repository: %s", project_path)
        return []
    except Exception as e:
        logger.warning("Error opening repository: %s", e)
        return []

    # Load mailmap if it exists
    mailmap = _load_mailmap(Path(project_path))

    # Collect raw contributor identities
    raw_identities: List[Dict[str, Any]] = []
    
    try:
        commit_iter = repo.iter_commits("--all" if use_all_branches else None)
        commit_count = 0

        for commit in commit_iter:
            # Enforce limit
            if max_commits and commit_count >= max_commits:
                logger.info(f"Reached commit limit ({max_commits}), stopping")
                break

            commit_count += 1

            # Extract author info
            try:
                raw_name = commit.author.name.strip() if commit.author.name else "Unknown"
                raw_email = commit.author.email.strip() if commit.author.email else ""
            except Exception:
                continue

            # Skip bots
            if "[bot]" in raw_name.lower():
                continue

            # Apply mailmap if available
            canonical_name, canonical_email = _apply_mailmap(mailmap, raw_name, raw_email)

            raw_identities.append({
                "name": raw_name,
                "email": _normalize_email(raw_email),
                "canonical_name": canonical_name,
                "canonical_email": _normalize_email(canonical_email),
                "commit_hash": commit.hexsha[:8],
                "commit_message": commit.message.strip()[:100] if commit.message else "",
                "commit_timestamp": commit.committed_date,
            })

        logger.info(f"Processed {commit_count} commits")

    except Exception as e:
        logger.warning("Error processing commits: %s", e)
        return []

    # Cluster contributors using similarity matching
    contributors = _cluster_contributors(raw_identities)
    
    logger.info(f"Found {len(contributors)} unique contributors after clustering")

    # Calculate percentages and format output
    total_commits = sum(c["commits"] for c in contributors)
    result = []

    for contributor in contributors:
        if total_commits > 0:
            contributor["percent"] = round((contributor["commits"] / total_commits) * 100, 2)
        else:
            contributor["percent"] = 0

        result.append(contributor)

    # Sort by commits descending
    result.sort(key=lambda x: x["commits"], reverse=True)

    return result


def _extract_github_username(email: str) -> Optional[str]:
    """Extract GitHub username from noreply email."""
    if not email or "users.noreply.github.com" not in email:
        return None

    local_part = email.split("@")[0]
    if "+" in local_part:
        return local_part.split("+")[-1]
    return local_part


def _extract_email_username(email: str) -> str:
    """Extract username part from email address."""
    if not email or "@" not in email:
        return ""
    return email.split("@")[0].lower()


def _load_mailmap(repo_path: Path) -> Dict[Tuple[str, str], Tuple[str, str]]:
    """
    Load Git mailmap file if it exists.
    
    Returns dict mapping (name, email) -> (canonical_name, canonical_email)
    """
    mailmap_path = repo_path / ".mailmap"
    mailmap = {}
    
    if not mailmap_path.exists():
        return mailmap
    
    try:
        with open(mailmap_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # Parse mailmap format: Proper Name <proper@email> Commit Name <commit@email>
                parts = line.split(">")
                if len(parts) >= 2:
                    canonical = parts[0].strip()
                    original = parts[1].strip()
                    
                    # Extract canonical name/email
                    if "<" in canonical:
                        can_name, can_email = canonical.split("<", 1)
                        can_name = can_name.strip()
                        can_email = can_email.strip()
                    else:
                        can_name = canonical
                        can_email = ""
                    
                    # Extract original name/email
                    if "<" in original:
                        orig_name, orig_email = original.split("<", 1)
                        orig_name = orig_name.strip()
                        orig_email = orig_email.strip()
                    else:
                        orig_name = original
                        orig_email = ""
                    
                    if orig_name or orig_email:
                        mailmap[(orig_name, orig_email)] = (can_name, can_email)
        
        logger.info(f"Loaded {len(mailmap)} entries from .mailmap")
    except Exception as e:
        logger.warning(f"Error loading .mailmap: {e}")
    
    return mailmap


def _apply_mailmap(
    mailmap: Dict[Tuple[str, str], Tuple[str, str]],
    name: str,
    email: str
) -> Tuple[str, str]:
    """Apply mailmap to get canonical name and email."""
    if not mailmap:
        return name, email
    
    # Try exact match
    key = (name, email.lower())
    if key in mailmap:
        return mailmap[key]
    
    # Try email-only match
    for (m_name, m_email), (c_name, c_email) in mailmap.items():
        if m_email and m_email == email.lower():
            return c_name or name, c_email or email
    
    return name, email


def _cluster_contributors(identities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Cluster contributor identities using similarity matching.
    
    Merges contributors based on:
    - Exact email match (canonical or original)
    - GitHub username from noreply emails
    - Email username similarity (e.g., jaidenlo@gmail.com and jaidenlo from noreply)
    - Name similarity within same email domain
    """
    if not identities:
        return []
    
    # Build initial clusters keyed by strongest identifier
    clusters: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    cluster_keys: Dict[str, str] = {}  # Maps various identifiers to cluster key
    
    for identity in identities:
        email = identity["canonical_email"] or identity["email"]
        name = identity["canonical_name"] or identity["name"]
        
        # Extract identifiers
        github_username = _extract_github_username(email)
        email_username = _extract_email_username(email)
        normalized_name = _normalize_name(name)
        
        # Find matching cluster
        cluster_key = None
        
        # Priority 1: GitHub username (strongest signal)
        if github_username:
            gh_key = f"gh:{github_username}"
            if gh_key in cluster_keys:
                cluster_key = cluster_keys[gh_key]
            else:
                cluster_keys[gh_key] = gh_key
                cluster_key = gh_key
        
        # Priority 2: Exact email match
        if not cluster_key and email:
            email_key = f"email:{email}"
            if email_key in cluster_keys:
                cluster_key = cluster_keys[email_key]
            else:
                # Check if email username matches existing GitHub username
                if email_username:
                    gh_key = f"gh:{email_username}"
                    if gh_key in cluster_keys:
                        cluster_key = cluster_keys[gh_key]
                        cluster_keys[email_key] = cluster_key
                
                if not cluster_key:
                    cluster_keys[email_key] = email_key
                    cluster_key = email_key
        
        # Priority 3: Email username match (e.g., jaidenlo@gmail.com matches jaidenlo noreply)
        if not cluster_key and email_username:
            username_key = f"user:{email_username}"
            if username_key in cluster_keys:
                cluster_key = cluster_keys[username_key]
            else:
                cluster_keys[username_key] = username_key
                cluster_key = username_key
        
        # Priority 4: Normalized name (weakest, only if nothing else matches)
        if not cluster_key and normalized_name:
            name_key = f"name:{normalized_name}"
            if name_key in cluster_keys:
                cluster_key = cluster_keys[name_key]
            else:
                cluster_keys[name_key] = name_key
                cluster_key = name_key
        
        if not cluster_key:
            cluster_key = f"unknown:{len(clusters)}"
        
        # Add all possible keys to the mapping to ensure future matches
        if github_username:
            cluster_keys[f"gh:{github_username}"] = cluster_key
        if email:
            cluster_keys[f"email:{email}"] = cluster_key
        if email_username:
            cluster_keys[f"user:{email_username}"] = cluster_key
        
        clusters[cluster_key].append(identity)
    
    # Second pass: merge clusters with similar names or related emails
    clusters = _merge_similar_clusters(clusters)
    
    # Merge each cluster into a single contributor record
    contributors = []
    
    for cluster_identities in clusters.values():
        # Collect all names, emails, etc.
        all_names: Set[str] = set()
        all_emails: Set[str] = set()
        all_github_usernames: Set[str] = set()
        history = []
        
        for identity in cluster_identities:
            if identity["name"]:
                all_names.add(identity["name"])
            if identity["canonical_name"]:
                all_names.add(identity["canonical_name"])
            
            if identity["email"]:
                all_emails.add(identity["email"])
            if identity["canonical_email"]:
                all_emails.add(identity["canonical_email"])
            
            gh = _extract_github_username(identity["email"])
            if gh:
                all_github_usernames.add(gh)
            gh = _extract_github_username(identity["canonical_email"])
            if gh:
                all_github_usernames.add(gh)
            
            history.append({
                "hash": identity["commit_hash"],
                "message": identity["commit_message"],
                "timestamp": identity["commit_timestamp"],
            })
        
        # Choose best name and email
        display_name = _choose_display_name(all_names, fallback="Unknown")
        primary_email = _choose_primary_email(all_emails, fallback="")
        github_username = sorted(all_github_usernames)[0] if all_github_usernames else None
        github_email = next((e for e in sorted(all_emails) if "github" in e), None)
        
        contributors.append({
            "name": display_name,
            "email": primary_email,
            "primary_email": primary_email,
            "github_username": github_username,
            "github_email": github_email,
            "commits": len(cluster_identities),
            "history": history,
            "total_lines_added": 0,
            "total_lines_deleted": 0,
            "files_modified": {},
            "all_emails": sorted(e for e in all_emails if e),
            "all_names": sorted(n for n in all_names if n),
        })
    
    return contributors


def _merge_similar_clusters(clusters: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Merge clusters that likely represent the same person.
    
    Uses heuristics like:
    - Similar names (e.g., "AnLaxina" and "Anilov Laxina")
    - Related email patterns
    """
    if len(clusters) <= 1:
        return clusters
    
    # Build a mapping of cluster key -> representative info
    cluster_info = {}
    for key, identities in clusters.items():
        all_names = set()
        all_emails = set()
        all_gh_users = set()
        
        for identity in identities:
            if identity["name"]:
                all_names.add(identity["name"].lower())
            if identity["canonical_name"]:
                all_names.add(identity["canonical_name"].lower())
            if identity["email"]:
                all_emails.add(identity["email"])
            if identity["canonical_email"]:
                all_emails.add(identity["canonical_email"])
            
            gh = _extract_github_username(identity["email"])
            if gh:
                all_gh_users.add(gh.lower())
        
        cluster_info[key] = {
            "names": all_names,
            "emails": all_emails,
            "gh_users": all_gh_users,
            "email_usernames": {_extract_email_username(e) for e in all_emails if e},
        }
    
    # Find clusters to merge (using union-find pattern)
    parent = {k: k for k in clusters.keys()}
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[py] = px
    
    # Compare all cluster pairs
    cluster_keys = list(clusters.keys())
    for i, key1 in enumerate(cluster_keys):
        for key2 in cluster_keys[i+1:]:
            info1 = cluster_info[key1]
            info2 = cluster_info[key2]
            
            # Check for name similarity
            for name1 in info1["names"]:
                for name2 in info2["names"]:
                    if _names_are_similar(name1, name2):
                        logger.debug(f"Merging clusters due to similar names: '{name1}' ~ '{name2}'")
                        union(key1, key2)
                        break
            
            # Check for email username overlap (e.g., aliffmlg and aliffrazak02 might have "aliff" in common)
            # This is weak but can help in some cases
            for user1 in info1["email_usernames"]:
                for user2 in info2["email_usernames"]:
                    # Check if one username contains the other (e.g., "anlaxina" in "anilovlaxina")
                    if user1 and user2 and len(user1) >= 4 and len(user2) >= 4:
                        if user1 in user2 or user2 in user1:
                            # Also check name similarity as confirmation
                            if any(_names_are_similar(n1, n2) for n1 in info1["names"] for n2 in info2["names"]):
                                logger.debug(f"Merging clusters due to username overlap: '{user1}' ~ '{user2}'")
                                union(key1, key2)
                                break
    
    # Merge clusters with same parent
    merged_clusters: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for key, identities in clusters.items():
        root = find(key)
        merged_clusters[root].extend(identities)
    
    return merged_clusters


def _names_are_similar(name1: str, name2: str) -> bool:
    """
    Check if two names are similar enough to be the same person.
    
    Examples:
    - "AnLaxina" and "Anilov Laxina" -> True
    - "kusshsatija" and "Kussh Satija" -> True
    - "Jaiden" and "Slimosaurus" -> False
    """
    if not name1 or not name2:
        return False
    
    n1 = name1.lower().strip()
    n2 = name2.lower().strip()
    
    # Exact match
    if n1 == n2:
        return True
    
    # Remove spaces and compare (e.g., "kusshsatija" == "kussh satija")
    n1_nospace = n1.replace(" ", "").replace("-", "").replace("_", "")
    n2_nospace = n2.replace(" ", "").replace("-", "").replace("_", "")
    
    if n1_nospace == n2_nospace:
        return True
    
    # One is a substring of the other (with spaces removed)
    if len(n1_nospace) >= 5 and len(n2_nospace) >= 5:
        if n1_nospace in n2_nospace or n2_nospace in n1_nospace:
            return True
    
    # Check for common significant substrings (e.g., "laxina" in both "AnLaxina" and "Anilov Laxina")
    # Extract all substrings of length 5+
    if len(n1_nospace) >= 5 and len(n2_nospace) >= 5:
        min_len = min(len(n1_nospace), len(n2_nospace))
        # Check for overlap of at least 70% of the shorter name
        threshold = max(5, int(min_len * 0.7))
        
        # Find longest common substring
        lcs_len = _longest_common_substring_length(n1_nospace, n2_nospace)
        if lcs_len >= threshold:
            return True
    
    # Check for common tokens (at least 2 significant tokens match)
    tokens1 = set(t for t in n1.split() if len(t) >= 3)
    tokens2 = set(t for t in n2.split() if len(t) >= 3)
    
    if tokens1 and tokens2:
        common_tokens = tokens1 & tokens2
        if len(common_tokens) >= min(len(tokens1), len(tokens2)):
            return True
    
    return False


def _longest_common_substring_length(s1: str, s2: str) -> int:
    """Find the length of the longest common substring between two strings."""
    if not s1 or not s2:
        return 0
    
    max_len = 0
    # Use a simple O(n*m) approach with rolling comparison
    for i in range(len(s1)):
        for j in range(len(s2)):
            length = 0
            while (i + length < len(s1) and 
                   j + length < len(s2) and 
                   s1[i + length] == s2[j + length]):
                length += 1
            max_len = max(max_len, length)
    
    return max_len


def _normalize_email(email: str) -> str:
    """Lowercase and strip email for consistent comparison."""
    return email.strip().lower() if email else ""


def _normalize_name(name: str) -> str:
    """Collapse whitespace and lowercase a name for matching."""
    return " ".join(name.split()).lower() if name else ""


def _choose_primary_email(emails: Set[str], fallback: str = "") -> str:
    """Prefer non-noreply emails, otherwise use any available fallback."""
    if not emails:
        return fallback

    non_noreply = [e for e in emails if "noreply" not in e]
    if non_noreply:
        return sorted(non_noreply)[0]

    return sorted(emails)[0]


def _choose_display_name(names: Set[str], fallback: str = "") -> str:
    """Pick a reasonable display name, avoiding generic placeholders."""
    if not names and fallback:
        return fallback

    cleaned = [n for n in names if n and n.strip().lower() not in {"unknown"}]
    if cleaned:
        return sorted(cleaned)[0]

    return fallback or "Unknown"
