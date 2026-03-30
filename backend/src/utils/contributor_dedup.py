"""Contributor deduplication utilities."""

import re
from collections import defaultdict
from typing import Optional, List, Dict, Set


def _normalize_email(email: str) -> str:
    """Normalize email to lowercase."""
    return email.lower().strip() if email else ""


def _extract_github_username(email: str) -> Optional[str]:
    """Extract GitHub username from noreply email."""
    if not email or "users.noreply.github.com" not in email:
        return None
    local_part = email.split("@")[0]
    if "+" in local_part:
        return local_part.split("+")[-1].lower()
    return local_part.lower()


def _extract_email_username(email: str) -> str:
    """Extract username part from email address."""
    if not email or "@" not in email:
        return ""
    return email.split("@")[0].lower()


def _normalize_name(name: str) -> str:
    """Normalize name for comparison."""
    name = name.lower().strip()
    name = re.sub(r"\d+", "", name)
    name = re.sub(r"[-_.]", " ", name)
    return name.strip()


def _names_are_similar(name1: str, name2: str) -> bool:
    """Check if two names likely belong to the same person."""
    n1 = _normalize_name(name1)
    n2 = _normalize_name(name2)

    if not n1 or not n2:
        return False
    if n1 == n2:
        return True

    n1_no_space = n1.replace(" ", "")
    n2_no_space = n2.replace(" ", "")
    if n1_no_space == n2_no_space:
        return True

    if len(n1_no_space) > 3 and len(n2_no_space) > 3:
        if n1_no_space in n2_no_space or n2_no_space in n1_no_space:
            return True

    parts1 = set(n1.split())
    parts2 = set(n2.split())
    if parts1 and parts2:
        for p1 in parts1:
            for p2 in parts2:
                if len(p1) > 2 and len(p2) > 2 and (p1 == p2 or p1 in p2 or p2 in p1):
                    return True
    return False


def _emails_are_related(email1: str, email2: str) -> bool:
    """Check if two emails likely belong to the same person."""
    e1 = _normalize_email(email1)
    e2 = _normalize_email(email2)

    if not e1 or not e2:
        return False
    if e1 == e2:
        return True

    gh1 = _extract_github_username(e1)
    gh2 = _extract_github_username(e2)
    if gh1 and gh2 and gh1 == gh2:
        return True

    user1 = _extract_email_username(e1)
    user2 = _extract_email_username(e2)
    if user1 and user2 and user1 == user2:
        return True

    if gh1 and user2 and gh1 == user2:
        return True
    if gh2 and user1 and gh2 == user1:
        return True

    return False


def _choose_display_name(names: Set[str]) -> str:
    """Choose the best display name from a set of names."""
    if not names:
        return "Unknown"
    names_with_spaces = [n for n in names if " " in n]
    if names_with_spaces:
        for name in names_with_spaces:
            if name[0].isupper():
                return name
        return names_with_spaces[0]
    return max(names, key=len)


def _choose_primary_email(emails: Set[str]) -> str:
    """Choose the best primary email from a set of emails."""
    if not emails:
        return ""
    non_noreply = [e for e in emails if "noreply" not in e.lower()]
    if non_noreply:
        return sorted(non_noreply)[0]
    return sorted(emails)[0]


def normalize_identity(identity: str) -> str:
    """Normalize an identity string for matching."""
    return identity.lower().strip() if identity else ""


def identity_matches(
    identity: str,
    *,
    name: Optional[str] = None,
    email: Optional[str] = None,
    github_username: Optional[str] = None,
    github_email: Optional[str] = None,
) -> bool:
    """Check whether an identity string matches contributor fields."""
    normalized = normalize_identity(identity)
    if not normalized:
        return False

    name_norm = name.strip() if name else ""
    email_norm = _normalize_email(email) if email else ""
    github_email_norm = _normalize_email(github_email) if github_email else ""
    gh_username_norm = normalize_identity(github_username) if github_username else ""

    identity_email = _normalize_email(normalized) if "@" in normalized else ""
    identity_username = _extract_email_username(identity_email or normalized)
    identity_gh = (
        _extract_github_username(identity_email or normalized) or identity_username
    )

    candidate_emails = {e for e in [email_norm, github_email_norm] if e}
    candidate_usernames = {u for u in [gh_username_norm] if u}

    for candidate_email in candidate_emails:
        candidate_usernames.add(_extract_email_username(candidate_email))
        gh_from_email = _extract_github_username(candidate_email)
        if gh_from_email:
            candidate_usernames.add(gh_from_email)

    if identity_email:
        for candidate_email in candidate_emails:
            if _emails_are_related(identity_email, candidate_email):
                return True

    if normalized in candidate_emails:
        return True
    if normalized in candidate_usernames:
        return True
    if identity_username and identity_username in candidate_usernames:
        return True
    if identity_gh and identity_gh in candidate_usernames:
        return True

    if name_norm:
        if _names_are_similar(normalized, name_norm):
            return True

    return False


def cluster_authors(raw_stats: List[Dict]) -> List[Dict]:
    """
    Cluster raw author stats by deduplicating similar identities.

    Args:
        raw_stats: List of {"author": "Name <email>", "added": int, "deleted": int}

    Returns:
        Deduplicated list with aggregated stats
    """
    parsed = []
    for stat in raw_stats:
        author_str = stat["author"]
        match = re.match(r"^(.+?)\s*<([^>]+)>$", author_str)
        if match:
            name = match.group(1).strip()
            email = match.group(2).strip()
        else:
            name = author_str.strip()
            email = ""
        parsed.append(
            {
                "name": name,
                "email": _normalize_email(email),
                "added": stat["added"],
                "deleted": stat["deleted"],
            }
        )

    n = len(parsed)
    parent = list(range(n))

    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[py] = px

    for i in range(n):
        for j in range(i + 1, n):
            p1, p2 = parsed[i], parsed[j]
            if (
                p1["email"]
                and p2["email"]
                and _emails_are_related(p1["email"], p2["email"])
            ):
                union(i, j)
                continue
            if p1["name"] and p2["name"] and _names_are_similar(p1["name"], p2["name"]):
                union(i, j)
                continue
            gh1 = _extract_github_username(p1["email"])
            gh2 = _extract_github_username(p2["email"])
            if gh1 and _names_are_similar(gh1, p2["name"]):
                union(i, j)
                continue
            if gh2 and _names_are_similar(gh2, p1["name"]):
                union(i, j)

    clusters = defaultdict(list)
    for i in range(n):
        clusters[find(i)].append(i)

    result = []
    for indices in clusters.values():
        all_names: Set[str] = set()
        all_emails: Set[str] = set()
        total_added = 0
        total_deleted = 0

        for idx in indices:
            p = parsed[idx]
            if p["name"]:
                all_names.add(p["name"])
            if p["email"]:
                all_emails.add(p["email"])
            total_added += p["added"]
            total_deleted += p["deleted"]

        display_name = _choose_display_name(all_names)
        primary_email = _choose_primary_email(all_emails)

        result.append(
            {
                "author": f"{display_name} <{primary_email}>"
                if primary_email
                else display_name,
                "display_name": display_name,
                "primary_email": primary_email,
                "total_lines_changed": total_added + total_deleted,
                "total_lines_added": total_added,
                "total_lines_deleted": total_deleted,
                "all_names": sorted(all_names),
                "all_emails": sorted(all_emails),
            }
        )

    result.sort(key=lambda x: x["total_lines_changed"], reverse=True)
    return result
