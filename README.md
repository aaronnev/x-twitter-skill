# X Personal Analytics Skill

Give your AI agent eyes on your X account — analytics, posts, mentions, followers — for **~$1-2/month**. Read-only by design. Official API only, no scraping, no suspension risk.

## What It Does

- **Read any tweet** — paste a URL, get the full content. No browser, no login, no screenshots
- **Thread reconstruction** — fetch entire conversations automatically
- **Morning briefing** — one command: posts + mentions + profile + follower delta (~$0.02)
- **Timeline analytics** — your recent posts with full engagement metrics
- **Mentions** — who's replying to or quoting you, with their follower count
- **Bookmarks** — save, list, and manage your bookmarked posts
- **Follower tracking** — daily count with delta over time
- **Accountability** — checks if you're spending too much time on X when you should be working
- **Budget controls** — 3 modes (guarded / relaxed / unlimited), daily spend tracking, dry-run on every command
- **Cost optimized** — persistent local store + incremental fetching = ~$1-2/mo

### Just ask your agent

You don't need to memorise commands. Just talk:

- *"What did my last 5 tweets do?"*
- *"Who mentioned me today?"*
- *"Read this thread: https://x.com/..."*
- *"Give me my morning X briefing"*
- *"How much have I spent on the API this week?"*
- *"Am I posting too much today?"*

Your agent reads [SKILL.md](SKILL.md) and figures out the right script.

## Install

```bash
git clone https://github.com/aaronnev/x-twitter-skill.git x-twitter
```

Works with [OpenClaw](https://openclaw.ai), [Claude Code](https://claude.ai/code), or any agent that reads skill files.

**[→ Setup guide](SETUP.md)** — step-by-step walkthrough for X Developer account, API keys, and budget configuration.

## Commands

| Command | What It Does | Cost |
|---------|-------------|------|
| `x_briefing.py` | Full morning briefing | ~$0.02 |
| `x_read.py URL` | Read any tweet by URL or ID | ~$0.005 |
| `x_read.py URL --thread` | Read full thread | ~$0.005-0.01 |
| `x_timeline.py recent` | Recent posts + engagement | ~$0.005 |
| `x_timeline.py top` | Top posts from local store | $0 |
| `x_timeline.py activity` | Accountability check | ~$0.005 |
| `x_mentions.py recent` | Recent mentions/replies | ~$0.005 |
| `x_bookmarks.py list` | Your saved bookmarks | ~$0.005 |
| `x_bookmarks.py add ID` | Bookmark a post | $0 |
| `x_user.py me` | Your profile stats | ~$0.01 |
| `x_user.py lookup USER` | Any user's profile | ~$0.01 |
| `x_setup.py --spend-report` | Weekly spend summary | $0 |
| `x_setup.py --budget-mode MODE` | Set budget mode | $0 |
| Any command `--dry-run` | Preview cost without API call | $0 |
| Any command `--no-budget` | Skip budget checks | $0 |

## Cost

X API v2 is pay-per-use. This skill keeps costs low:

| Usage | Daily | Monthly |
|-------|-------|---------|
| Morning briefing only | $0.02 | $0.60 |
| Briefing + a few checks | $0.04 | $1.20 |
| Heavy monitoring | $0.10 | $3.00 |

Cost scales with **check frequency**, not followers. 100 followers or 100K — same price.

Three budget modes to control spend:
- **Guarded** (default) — warns and blocks at daily limit
- **Relaxed** — warns but keeps going
- **Unlimited** — no limits

## How It Works

```
You ask your agent → Agent reads SKILL.md → runs the right script via uv
                                                      ↓
                                              Script hits X API v2
                                                      ↓
                                         Response stored locally (data/)
                                                      ↓
                                           Clean output → agent → you
```

**3 layers of cost optimization:**
1. **Persistent store** — tweets saved locally on first fetch, never re-fetched
2. **Incremental fetching** — `since_id` means only new tweets cost anything
3. **Budget guard** — tracks every API call, blocks when daily limit hit

### Why not scraping?

X is actively detecting and suspending accounts that use automated scraping, cookie-based tools, or browser automation. This skill uses OAuth 1.0a with your own API keys — no cookies, no headless browsers, no risk.

<img src="assets/nikitabier-api-vs-scraping.png" alt="@nikitabier on API vs scraping policy" width="500">

> @nikitabier [confirmed](https://x.com/nikitabier/status/2022502068486074617): *"Use the official API all you want. But any form of scraping or search that is automated will get caught."*

## FAQ

**Will this cost more if I have a big account?**
No. API cost is per-request, not per-follower.

**What if I go viral?**
Mentions might paginate (more API calls), and the briefing will flag it.

**What's the most expensive thing?**
Reading long threads. A 500-tweet thread = ~5 paginated calls ($0.025).

**Can I see exactly what I've spent?**
`uv run scripts/x_setup.py --spend-report` — daily breakdown with monthly projection.

## File Structure

```
x-twitter/
├── SKILL.md              # Agent skill manifest
├── AGENTS.md             # Machine-readable command reference
├── SETUP.md              # Detailed setup walkthrough
├── CONTRIBUTING.md       # How to contribute
├── scripts/
│   ├── x_common.py       # Shared utilities
│   ├── x_setup.py        # Setup wizard + spend reports
│   ├── x_briefing.py     # Combined morning briefing
│   ├── x_read.py         # Read any tweet or thread
│   ├── x_timeline.py     # Posts + engagement + accountability
│   ├── x_mentions.py     # Mentions and replies
│   ├── x_user.py         # Profile + follower tracking
│   └── x_bookmarks.py    # Bookmark management
└── references/
    └── x-api-quickref.md # API endpoint reference
```

## Roadmap

- **Real-time mention streaming** via Filtered Stream — mentions pushed, not polled
- **Engagement velocity alerts** — flag posts getting unusual traction early
- **Quote tweet detection** — surface when someone quotes your post
- **Competitor watch** — track accounts, surface their top posts

## Credits

Built by [@aaronnev_](https://x.com/aaronnev_) with [Claude Code](https://claude.ai/code) + [OpenClaw](https://openclaw.ai).

Powered by [tweepy](https://github.com/tweepy/tweepy) and [uv](https://github.com/astral-sh/uv).

## License

MIT
