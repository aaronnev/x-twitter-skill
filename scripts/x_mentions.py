#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "tweepy>=4.14.0",
# ]
# ///
"""X (Twitter) mentions — who's replying to and talking about you."""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import tweepy

CONFIG_DIR = Path.home() / ".openclaw" / "skills-config" / "x-twitter"
CONFIG_PATH = CONFIG_DIR / "config.json"
DATA_DIR = CONFIG_DIR / "data"
MENTIONS_PATH = DATA_DIR / "mentions.json"
USAGE_PATH = DATA_DIR / "usage.json"

TWEET_FIELDS = [
    "created_at", "public_metrics", "text", "author_id",
    "conversation_id", "in_reply_to_user_id", "referenced_tweets",
]

USER_FIELDS = ["username", "name", "verified", "public_metrics"]


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


def load_store() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if MENTIONS_PATH.exists():
        return json.loads(MENTIONS_PATH.read_text())
    return {}


def save_store(store: dict):
    MENTIONS_PATH.write_text(json.dumps(store, indent=2))


def track_usage(tweet_reads: int = 0, user_reads: int = 0) -> dict:
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


def check_budget(config: dict, force: bool = False) -> bool:
    if force:
        return True
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if USAGE_PATH.exists():
        usage = json.loads(USAGE_PATH.read_text())
        if today in usage and usage[today]["est_cost"] >= config.get("daily_budget", 0.25):
            print(f"Daily budget exceeded (${usage[today]['est_cost']:.3f} / ${config['daily_budget']:.2f})")
            print("Use --force to override.")
            return False
    return True


def format_time(dt) -> str:
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    return dt.astimezone().strftime("%Y-%m-%d %H:%M %Z")


def time_ago(dt) -> str:
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    diff = now - dt
    if diff.total_seconds() < 60:
        return f"{int(diff.total_seconds())}s ago"
    if diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() / 60)}m ago"
    if diff.total_seconds() < 86400:
        return f"{int(diff.total_seconds() / 3600)}h ago"
    return f"{diff.days}d ago"


def format_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n/1_000:.1f}K"
    return f"{n:,}"


def cmd_recent(args):
    config = load_config()
    if not config:
        return

    if args.dry_run:
        cost = "$0.005" if not args.context else "$0.005-0.030"
        print(f"[DRY RUN] x_mentions.py recent")
        print(f"  Would cost: ~{cost} (1 tweet read{' + context lookups' if args.context else ''})")
        if args.context:
            print(f"  Tip: skip --context to save ~$0.025 — only adds parent tweet text")
        budget_warning(config)
        return

    if not check_budget(config, args.force):
        return

    store = load_store()
    client = get_client(config)
    user_id = config["user_id"]

    kwargs = {
        "id": user_id,
        "max_results": min(args.max, 100),
        "tweet_fields": TWEET_FIELDS,
        "expansions": ["author_id"],
        "user_fields": USER_FIELDS,
        "user_auth": True,
    }

    if args.hours:
        kwargs["start_time"] = datetime.now(timezone.utc) - timedelta(hours=args.hours)

    since_id = config.get("last_mention_id")
    if since_id and not args.hours and not args.no_cache:
        kwargs["since_id"] = since_id

    api_calls = 0
    try:
        resp = client.get_users_mentions(**kwargs)
        api_calls = 1
    except tweepy.errors.HTTPException as e:
        if "402" in str(e):
            print("Error: No credits on your X developer account.")
            print("Add credits at https://developer.x.com to use tweet endpoints.")
            return
        print(f"Error: {e}")
        return
    except tweepy.errors.TweepyException as e:
        print(f"Error: {e}")
        return

    day_usage = track_usage(tweet_reads=api_calls)
    budget_warning(config)

    # Build author lookup from includes
    authors = {}
    if resp.includes and "users" in resp.includes:
        for user in resp.includes["users"]:
            authors[str(user.id)] = {
                "username": user.username,
                "name": user.name,
                "followers": user.public_metrics["followers_count"] if user.public_metrics else 0,
            }

    if not resp.data:
        if not args.no_cache and store:
            stored = sorted(store.values(), key=lambda t: t.get("created_at", ""), reverse=True)
            if args.hours:
                cutoff = (datetime.now(timezone.utc) - timedelta(hours=args.hours)).isoformat()
                stored = [t for t in stored if t.get("created_at", "") >= cutoff]
            stored = stored[:args.max]
            if stored:
                print(f"Your Mentions (from local store, {len(stored)})")
                print("=" * 50)
                for i, m in enumerate(stored, 1):
                    print_mention(m, i)
                print(f"---\n(Served from local store — 0 API calls)")
                print(f"Today's spend: ${day_usage['est_cost']:.3f}")
                return
        print("No new mentions found.")
        print(f"---\nEst. API cost: ~${api_calls * 0.005:.3f}")
        print(f"Today's spend: ${day_usage['est_cost']:.3f}")
        return

    # Store mentions
    mentions = []
    for tweet in resp.data:
        tid = str(tweet.id)
        author = authors.get(str(tweet.author_id), {})
        ref_type = "mention"
        if tweet.referenced_tweets:
            for ref in tweet.referenced_tweets:
                if ref.type == "replied_to":
                    ref_type = "reply"
                elif ref.type == "quoted":
                    ref_type = "quote"

        data = {
            "id": tid,
            "text": tweet.text,
            "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
            "author_id": str(tweet.author_id),
            "author_username": author.get("username", "unknown"),
            "author_name": author.get("name", ""),
            "author_followers": author.get("followers", 0),
            "type": ref_type,
            "metrics": dict(tweet.public_metrics) if tweet.public_metrics else {},
            "stored_at": datetime.now(timezone.utc).isoformat(),
        }
        store[tid] = data
        mentions.append(data)

    save_store(store)

    # Update since_id
    if mentions:
        max_id = max(m["id"] for m in mentions)
        if not since_id or int(max_id) > int(since_id):
            config["last_mention_id"] = max_id
            save_config(config)

    # Context fetching (optional)
    context_calls = 0
    if args.context:
        context_limit = 5
        for m in mentions[:context_limit]:
            if m["type"] == "reply" and m.get("metrics", {}).get("reply_count", 0) >= 0:
                # Try to get the tweet being replied to
                try:
                    for ref in resp.data:
                        if str(ref.id) == m["id"] and ref.referenced_tweets:
                            parent_id = ref.referenced_tweets[0].id
                            parent_resp = client.get_tweet(
                                id=parent_id,
                                tweet_fields=["text", "author_id", "created_at"],
                                user_auth=True,
                            )
                            context_calls += 1
                            if parent_resp.data:
                                m["context_text"] = parent_resp.data.text
                            break
                except Exception:
                    pass
        if context_calls:
            track_usage(tweet_reads=context_calls)
            day_usage = json.loads(USAGE_PATH.read_text()).get(
                datetime.now(timezone.utc).strftime("%Y-%m-%d"), {})

    # Display
    header = "Your Mentions"
    if args.hours:
        header += f" (last {args.hours}h)"
    print(f"{header} ({len(mentions)})")
    print("=" * 50)

    type_counts = {"reply": 0, "quote": 0, "mention": 0}
    for i, m in enumerate(mentions, 1):
        print_mention(m, i)
        type_counts[m.get("type", "mention")] += 1

    total_calls = api_calls + context_calls
    total_cost = total_calls * 0.005
    print(f"---")
    print(f"Summary: {len(mentions)} mentions | {type_counts['reply']} replies, {type_counts['quote']} quotes, {type_counts['mention']} direct")
    if total_cost > 0.02:
        print(f"Est. API cost: ~${total_cost:.3f} ({total_calls} tweet reads) [$$$ EXPENSIVE]")
        print(f"  Tip: skip --context next time to reduce cost")
    else:
        print(f"Est. API cost: ~${total_cost:.3f} ({total_calls} tweet reads)")
    print(f"Today's spend: ${day_usage.get('est_cost', 0):.3f}")


def print_mention(m: dict, index: int):
    """Print a single mention."""
    author = f"@{m.get('author_username', 'unknown')}"
    followers = m.get("author_followers", 0)
    mtype = m.get("type", "mention")

    text = m["text"]
    if len(text) > 200:
        text = text[:197] + "..."

    type_label = {"reply": "replied to your post", "quote": "quoted your post", "mention": "mentioned you"}
    print(f"{index}. {author} {type_label.get(mtype, 'mentioned you')}:")
    print(f"   \"{text}\"")
    print(f"   Posted: {format_time(m['created_at'])} ({time_ago(m['created_at'])})")
    print(f"   Their followers: {format_number(followers)}")

    if "context_text" in m:
        ctx = m["context_text"]
        if len(ctx) > 100:
            ctx = ctx[:97] + "..."
        print(f"   In reply to: \"{ctx}\"")

    print(f"   https://x.com/{m.get('author_username', 'i')}/status/{m['id']}")
    print()


def main():
    parser = argparse.ArgumentParser(description="X mentions — replies & mentions")
    parser.add_argument("--force", action="store_true", help="Override daily budget guard")
    parser.add_argument("--no-cache", action="store_true", help="Skip local store")
    parser.add_argument("--dry-run", action="store_true", help="Show estimated cost without making API calls")
    subparsers = parser.add_subparsers(dest="command", required=True)

    recent_p = subparsers.add_parser("recent", help="Recent mentions")
    recent_p.add_argument("--max", type=int, default=20, help="Max mentions (default: 20)")
    recent_p.add_argument("--hours", type=int, help="Only mentions from last N hours")
    recent_p.add_argument("--context", action="store_true", help="Fetch parent tweet for replies (costs extra)")

    args = parser.parse_args()
    if args.command == "recent":
        cmd_recent(args)


if __name__ == "__main__":
    main()
