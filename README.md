# X Personal Analytics Skill

Give your AI agent eyes on your X account — analytics, posts, mentions, followers — for **~$1-2/month**. Official API only, no scraping, no suspension risk. Built after @nikitabier [confirmed](https://x.com/nikitabier/status/2022502068486074617) automated scraping will get accounts suspended — this skill uses only the official X API v2.

<img src="assets/nikitabier-api-vs-scraping.png" alt="@nikitabier: Use the official API all you want. But any form of scraping or search that is automated will get caught currently." width="500">

Works with any AI agent — [OpenClaw](https://openclaw.ai), Claude Code, Codex, or anything that reads a [SKILL.md](http://skill.md/).

## What It Does

- **Timeline**: Your recent posts with full engagement metrics (impressions, likes, RTs, replies, quotes, bookmarks)
- **Mentions**: Who's replying to or quoting you, with their follower count
- **Read any tweet**: Fetch any tweet or thread by URL — with reply context and quote tweets
- **Bookmarks**: Save, list, and manage your bookmarked posts
- **Morning Briefing**: One command for posts + mentions + profile + follower delta (~$0.02)
- **Follower Tracking**: Daily follower count with delta tracking over time
- **Accountability**: Checks if you're spending too much time on X when you should be working
- **Cost Optimized**: Persistent local store + incremental fetching = minimal API costs (~$1-2/mo)

### Why Not Scraping / Bird CLI?

X is actively detecting and suspending accounts that use automated scraping, cookie-based tools, or browser automation. The official API is the only safe path for programmatic access. This skill uses OAuth 1.0a with your own API keys — no cookies, no headless browsers, no risk.

## Setup

See **[SETUP.md](SETUP.md)** for a detailed step-by-step guide including X Developer Console walkthrough, API credit loading, and budget configuration.

Quick version:

```bash
# 1. Clone the skill
cd ~/.openclaw/workspace/skills  # or wherever you keep skills
git clone https://github.com/aaronnev/x-twitter-skill.git x-twitter

# 2. Run setup (requires uv: curl -LsSf https://astral.sh/uv/install.sh | sh)
uv run scripts/x_setup.py

# 3. Test it
uv run scripts/x_user.py me
```

## Cost

X API v2 uses pay-per-use pricing:
- Tweet reads: ~$0.005 per request (up to 100 tweets per request)
- User reads: ~$0.01 per request
This skill minimizes costs with:
- **Persistent store**: tweets fetched once, stored forever locally
- **Incremental fetching**: `since_id` means only new tweets are fetched
- **Daily budget guard**: blocks requests when daily limit is hit
- **Budget tiers**: lite ($0.03/day), standard ($0.10/day), intense ($0.25/day)
- **Budget modes**: guarded (default — warn + block), relaxed (warn only), unlimited (no limits)

Typical monthly cost: **~$1-2** for daily briefings.

### How Costs Scale

Cost scales with **check frequency**, not content volume. Whether you have 100 or 100K followers, each API call costs the same.

- **Morning briefing**: $0.02/day ($0.60/mo) — 2 tweet reads + 1 user read
- **Briefing + a few checks**: $0.04/day ($1.20/mo)
- **Reading threads**: $0.005-0.010 per thread (50 tweets = 1 call, 500 = 5 paginated)
The biggest cost driver is curiosity — reading threads, checking mentions, looking up users. The sweet spot is accountability + morning briefing = $0.02-0.03/day.

## Commands

| Command | What It Does | API Cost |
|---------|-------------|----------|
| `x_briefing.py` | Full morning briefing (posts + mentions + profile) | ~$0.02 |
| `x_timeline.py recent` | Recent posts + engagement | ~$0.005 |
| `x_timeline.py top` | Top posts from local store | $0 |
| `x_timeline.py activity` | Accountability check | ~$0.005 |
| `x_timeline.py refresh ID` | Update one tweet's metrics | ~$0.005 |
| `x_mentions.py recent` | Recent mentions/replies | ~$0.005 |
| `x_mentions.py recent --context` | Mentions + parent tweets | ~$0.005-0.03 |
| `x_read.py URL/ID` | Read any tweet | ~$0.005 |
| `x_read.py URL/ID --thread` | Read full thread | ~$0.005-0.010 |
| `x_bookmarks.py list` | Your saved bookmarks | ~$0.005 |
| `x_bookmarks.py add ID` | Bookmark a post | $0 |
| `x_bookmarks.py remove ID` | Remove bookmark | $0 |
| `x_user.py me` | Your profile stats | ~$0.01 |
| `x_user.py me --track` | Profile + save follower delta | ~$0.01 |
| `x_user.py lookup USER` | Any user's profile | ~$0.01 |
| `x_setup.py --spend-report` | Weekly spend summary | $0 |
| `x_setup.py --version` | Print version | $0 |
| `x_setup.py --budget-mode MODE` | Set budget mode (guarded/relaxed/unlimited) | $0 |
| Any command `--dry-run` | Preview cost without API call | $0 |
| Any command `--no-budget` | Skip all budget checks/warnings | $0 |

## How It Works

### Architecture

The skill talks directly to the X API v2 using OAuth 1.0a (your API keys). No middlemen, no third-party proxies.

```
You ask your agent → Agent reads SKILL.md → runs the right script via uv
                                                      ↓
                                              Script hits X API v2
                                                      ↓
                                         Response stored locally (data/)
                                                      ↓
                                           Clean output → agent → you
```

### Cost Optimization (3 layers)

1. **Persistent local store** — Every tweet/mention gets saved to `data/tweets.json` on first fetch. Subsequent requests serve from local storage. A tweet is never re-fetched unless you explicitly ask (`refresh`).

2. **Incremental `since_id` fetching** — Each fetch stores the newest tweet ID. Next time, the API only returns tweets newer than that. First run pulls your recent history; after that, only new posts cost anything.

3. **Daily budget guard** — Tracks every API call in `data/usage.json`. If your daily spend hits the limit, the skill warns you and stops making calls (override with `--force`).

### Accountability Mode

`x_timeline.py activity` checks your recent posting activity and tells the agent:
- When you last posted
- How many posts today / this hour
- Whether you've been spending too much time on X

The agent can use this to nudge you back to work.

## FAQ

**Will this cost more if I have a big account?**
No. API cost is per-request, not per-follower. 100 followers or 100K — same price.

**What if I go viral?**
Mentions might paginate (more API calls to fetch them all), and the briefing will flag it. For high-frequency monitoring, consider the Filtered Stream endpoint (see Roadmap).

**What's the most expensive thing?**
Reading long threads with `--thread` + using `--context` on mentions. A 500-tweet thread takes ~5 paginated calls ($0.025). Context fetching adds $0.005 per reply thread.

**Can I see exactly what I've spent?**
Yes. `uv run scripts/x_setup.py --spend-report` shows daily breakdown with bar chart and monthly projection.

## File Structure

```
x-twitter/
├── SKILL.md              # OpenClaw skill manifest
├── AGENTS.md             # AI agent reference (machine-readable)
├── SETUP.md              # Step-by-step setup walkthrough
├── CONTRIBUTING.md       # How to contribute
├── README.md             # This file
├── LICENSE               # MIT
├── .gitignore
├── scripts/
│   ├── x_common.py       # Shared utilities (config, budget, formatting)
│   ├── x_setup.py        # Credential setup, validation, spend reports
│   ├── x_timeline.py     # Posts + engagement + accountability
│   ├── x_mentions.py     # Mentions and replies
│   ├── x_user.py         # Profile info + follower tracking
│   ├── x_read.py         # Read any tweet or thread by URL/ID
│   ├── x_bookmarks.py    # Bookmark management
│   └── x_briefing.py     # Combined morning briefing
└── references/
    └── x-api-quickref.md # API endpoint reference

# Config (per-user, NOT in repo):
~/.openclaw/skills-config/x-twitter/
├── config.json           # Credentials + settings (0600 permissions)
└── data/
    ├── tweets.json       # Persistent tweet store
    ├── mentions.json     # Persistent mention store
    ├── bookmarks.json    # Persistent bookmark store
    └── usage.json        # Daily API cost tracking
```

## Prerequisites

- [uv](https://astral.sh/uv) — Python package runner (handles dependencies automatically)
- X API developer account with credits loaded at [developer.x.com](https://developer.x.com)
- Any AI agent that reads [SKILL.md](http://skill.md/) ([OpenClaw](https://openclaw.ai), Claude Code, Codex, etc.)

## Roadmap

- **Real-time mention streaming** via Filtered Stream (`GET /2/tweets/search/stream`) — set rule `to:USERNAME`, get mentions pushed instead of polling. Eliminates cron-based checking. 1,000 rules available.
- **Engagement velocity alerts** — flag posts getting unusual traction early
- **Quote tweet detection** — surface when someone quotes your post
- **Competitor watch** — track accounts, surface their top posts

## Credits

Built by [@aaronnev_](https://x.com/aaronnev_) with [Claude Code](https://claude.ai/code) (Claude Opus 4.6).

Uses [tweepy](https://github.com/tweepy/tweepy) for X API v2 access and [uv](https://github.com/astral-sh/uv) for zero-config Python script execution.

## License

MIT
