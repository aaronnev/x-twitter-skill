#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "tweepy>=4.14.0",
# ]
# ///
"""X (Twitter) user profile info and follower tracking."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import tweepy

CONFIG_DIR = Path.home() / ".openclaw" / "skills-config" / "x-twitter"
CONFIG_PATH = CONFIG_DIR / "config.json"
DATA_DIR = CONFIG_DIR / "data"
USAGE_PATH = DATA_DIR / "usage.json"

USER_FIELDS = [
    "created_at", "description", "location", "public_metrics",
    "profile_image_url", "url", "verified", "verified_type",
]


SCRIPT_DIR = Path(__file__).resolve().parent


def load_config() -> dict | None:
    if not CONFIG_PATH.exists():
        print(f"Error: No config found at {CONFIG_PATH}")
        print(f"Run: uv run {SCRIPT_DIR / 'x_setup.py'}")
        return None
    return json.loads(CONFIG_PATH.read_text())


def save_config(config: dict):
    CONFIG_PATH.write_text(json.dumps(config, indent=2))


def get_client(config: dict) -> tweepy.Client:
    return tweepy.Client(
        bearer_token=config.get("bearer_token"),
        consumer_key=config["api_key"],
        consumer_secret=config["api_secret"],
        access_token=config["access_token"],
        access_token_secret=config["access_secret"],
        wait_on_rate_limit=True,
    )


def track_usage(tweet_reads: int = 0, user_reads: int = 0):
    """Track daily API usage."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    usage = {}
    if USAGE_PATH.exists():
        usage = json.loads(USAGE_PATH.read_text())
    if today not in usage:
        usage[today] = {"tweet_reads": 0, "user_reads": 0, "est_cost": 0.0}
    usage[today]["tweet_reads"] += tweet_reads
    usage[today]["user_reads"] += user_reads
    usage[today]["est_cost"] = (usage[today]["tweet_reads"] * 0.005 +
                                 usage[today]["user_reads"] * 0.01)
    USAGE_PATH.write_text(json.dumps(usage, indent=2))
    return usage[today]


def budget_warning(config: dict):
    """Print budget warning at 50%, 80%, 100% thresholds."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    budget = config.get("daily_budget", 0.25)
    if not USAGE_PATH.exists() or budget <= 0:
        return
    usage = json.loads(USAGE_PATH.read_text())
    if today not in usage:
        return
    cost = usage[today].get("est_cost", 0.0)
    pct = cost / budget * 100
    if pct >= 100:
        print(f"[!] BUDGET EXCEEDED: ${cost:.3f} / ${budget:.2f} ({pct:.0f}%)")
    elif pct >= 80:
        print(f"[!] Budget warning: ${cost:.3f} / ${budget:.2f} ({pct:.0f}%) — approaching limit")
    elif pct >= 50:
        print(f"[i] Budget note: ${cost:.3f} / ${budget:.2f} ({pct:.0f}%) used today")


def check_budget(config: dict) -> bool:
    """Check if daily budget is exceeded. Returns True if OK to proceed."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if USAGE_PATH.exists():
        usage = json.loads(USAGE_PATH.read_text())
        if today in usage and usage[today]["est_cost"] >= config.get("daily_budget", 0.25):
            print(f"Daily budget exceeded (${usage[today]['est_cost']:.3f} / ${config['daily_budget']:.2f})")
            print("Use --force to override.")
            return False
    return True


def format_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n/1_000:.1f}K"
    return f"{n:,}"


def cmd_me(args):
    config = load_config()
    if not config:
        return

    if args.dry_run:
        print("[DRY RUN] x_user.py me")
        print(f"  Would cost: ~$0.010 (1 user read)")
        budget_warning(config)
        return

    if not args.force and not check_budget(config):
        return

    client = get_client(config)
    resp = client.get_me(user_fields=USER_FIELDS, user_auth=True)
    day_usage = track_usage(user_reads=1)
    budget_warning(config)

    if not resp.data:
        print("Error: Could not retrieve profile.")
        return

    u = resp.data
    pm = u.public_metrics

    print(f"Profile: {u.name} (@{u.username})")
    print("=" * 40)
    if u.description:
        print(f"Bio: {u.description}")
    if u.location:
        print(f"Location: {u.location}")
    if u.created_at:
        print(f"Joined: {u.created_at.strftime('%B %Y')}")
    if u.url:
        print(f"URL: {u.url}")
    print()

    followers = pm["followers_count"]
    following = pm["following_count"]
    tweets = pm["tweet_count"]
    listed = pm["listed_count"]

    # Follower delta tracking
    delta_str = ""
    if True:  # Always show delta if history exists
        history = config.get("follower_history", [])
        if history:
            last = history[-1]
            diff = followers - last["followers"]
            if diff > 0:
                delta_str = f"  (+{diff} since {last['date']})"
            elif diff < 0:
                delta_str = f"  ({diff} since {last['date']})"

    print(f"Followers:  {format_number(followers)}{delta_str}")
    print(f"Following:  {format_number(following)}")
    print(f"Posts:      {format_number(tweets)}")
    print(f"Listed:     {format_number(listed)}")
    print()
    print(f"https://x.com/{u.username}")

    # Track follower history if --track
    if args.track:
        history = config.get("follower_history", [])
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # Don't duplicate same-day entries
        if not history or history[-1]["date"] != today:
            history.append({
                "date": today,
                "followers": followers,
                "following": following,
                "posts": tweets,
            })
            # Keep last 90 entries
            config["follower_history"] = history[-90:]
            save_config(config)
            print("\n(Follower history updated)")

    print(f"\n---\nEst. API cost: ~$0.010 (1 user read)")
    print(f"Today's spend: ${day_usage['est_cost']:.3f}")


def cmd_lookup(args):
    config = load_config()
    if not config:
        return

    if args.dry_run:
        print(f"[DRY RUN] x_user.py lookup {args.username}")
        print(f"  Would cost: ~$0.010 (1 user read)")
        budget_warning(config)
        return

    if not args.force and not check_budget(config):
        return

    client = get_client(config)
    username = args.username.lstrip("@")

    try:
        resp = client.get_user(username=username, user_fields=USER_FIELDS)
    except tweepy.errors.HTTPException as e:
        if "402" in str(e):
            print("Error: No credits on your X developer account.")
            print("Add credits at https://developer.x.com to use this endpoint.")
            return
        raise
    day_usage = track_usage(user_reads=1)
    budget_warning(config)

    if not resp.data:
        print(f"Error: User @{username} not found.")
        return

    u = resp.data
    pm = u.public_metrics

    print(f"Profile: {u.name} (@{u.username})")
    print("=" * 40)
    if u.description:
        print(f"Bio: {u.description}")
    if u.location:
        print(f"Location: {u.location}")
    if u.created_at:
        print(f"Joined: {u.created_at.strftime('%B %Y')}")
    if u.url:
        print(f"URL: {u.url}")
    print()
    print(f"Followers:  {format_number(pm['followers_count'])}")
    print(f"Following:  {format_number(pm['following_count'])}")
    print(f"Posts:      {format_number(pm['tweet_count'])}")
    print(f"Listed:     {format_number(pm['listed_count'])}")
    print()
    print(f"https://x.com/{u.username}")
    print(f"\n---\nEst. API cost: ~$0.010 (1 user read)")
    print(f"Today's spend: ${day_usage['est_cost']:.3f}")


def main():
    parser = argparse.ArgumentParser(description="X user profile info")
    parser.add_argument("--force", action="store_true", help="Override daily budget guard")
    parser.add_argument("--dry-run", action="store_true", help="Show estimated cost without making API calls")
    subparsers = parser.add_subparsers(dest="command", required=True)

    me_parser = subparsers.add_parser("me", help="Your profile stats")
    me_parser.add_argument("--track", action="store_true", help="Save follower count for delta tracking")

    lookup_parser = subparsers.add_parser("lookup", help="Look up any user")
    lookup_parser.add_argument("username", help="X handle (with or without @)")

    args = parser.parse_args()
    if args.command == "me":
        cmd_me(args)
    elif args.command == "lookup":
        cmd_lookup(args)


if __name__ == "__main__":
    main()
