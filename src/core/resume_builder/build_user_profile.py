#!/usr/bin/env python3
"""
Stage 1: User Profile

Interactive CLI script to collect user profile information for the resume
pipeline and save it as `user_profile.json` (or a custom path).

Usage (default output: ./user_profile.json):

    python build_user_profile.py

Or with a custom output path:

    python build_user_profile.py --output path/to/user_profile.json --overwrite
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional


def prompt(text: str, default: Optional[str] = None, required: bool = False) -> str:
    """
    Simple prompt wrapper that supports defaults and required fields.
    """
    while True:
        if default:
            raw = input(f"{text} [{default}]: ").strip()
            value = raw if raw else default
        else:
            value = input(f"{text}: ").strip()

        if required and not value:
            print("This field is required. Please enter a value.")
            continue

        return value


def build_user_profile_interactive() -> Dict[str, Any]:
    """
    Ask the user a series of questions and return the user_profile dict.
    """
    print("\n=== Stage 1: User Profile Setup ===\n")
    print("Please enter the information to be stored in user_profile.json.\n"
          "Press ENTER to leave optional fields blank.\n")

    name = prompt("Full name", required=True)
    title = prompt("Professional title (e.g., 'Software Engineer | Data-Driven Developer')", required=True)
    location = prompt("Location (City, Region, Country)", required=True)
    email = prompt("Email", required=True)
    phone = prompt("Phone number (with country code)", required=False)

    print("\n--- Online Presence (optional) ---")
    github = prompt("GitHub URL", default="", required=False)
    linkedin = prompt("LinkedIn URL", default="", required=False)
    portfolio = prompt("Portfolio/Personal site URL", default="", required=False)

    print("\n--- Summary ---")
    print("Write a 2–4 sentence professional summary or objective.")
    print("Tip: You can keep it one line here; you may refine it later in the canvas.\n")
    summary = prompt("Summary", required=True)

    links: Dict[str, str] = {}
    if github:
        links["github"] = github
    if linkedin:
        links["linkedin"] = linkedin
    if portfolio:
        links["portfolio"] = portfolio

    profile: Dict[str, Any] = {
        "name": name,
        "title": title,
        "location": location,
        "email": email,
        "phone": phone,
        "links": links,
        "summary": summary,
    }

    return profile


def write_user_profile(profile: Dict[str, Any], output_path: Path, overwrite: bool = False) -> None:
    """
    Write the profile dict to output_path as pretty JSON.
    """
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"Refusing to overwrite existing file: {output_path}\n"
            f"Use --overwrite to replace it."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage 1: Build user_profile.json for the resume pipeline."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="user_profile.json",
        help="Path to write the user_profile.json file (default: ./user_profile.json).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing user_profile.json file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    output_path = Path(args.output).expanduser().resolve()
    try:
        profile = build_user_profile_interactive()
        write_user_profile(profile, output_path, overwrite=args.overwrite)
    except FileExistsError as e:
        print(e)
        return

    print(f"\n✅ User profile written to: {output_path}")
    print("You can now use this file as input for Stage 2 (Build Raw Resume Data).\n")


if __name__ == "__main__":
    main()
