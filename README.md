# X Personal Analytics Skill

Your AI agent can't read Twitter. Links are opaque, threads are a mess, and there's no way to check how your posts are doing without opening the app and doomscrolling.

This fixes that. It gives your agent ([Claude Code](https://claude.ai/code), [OpenClaw](https://openclaw.ai), or anything that reads a SKILL.md) full read access to your X account via the official API. No scraping, no browser automation, no suspension risk. Read-only — it never posts on your behalf.

Costs about **$1-2/month**.

> Agents: see [AGENTS.md](AGENTS.md) for command reference.

## What It Does

- **Read any tweet** — paste a URL, get the full content. No browser, no login, no screenshots
- **Thread reconstruction** — fetch entire conversations automatically
- **Morning briefing** — one command: posts + mentions + profile + follower delta (~$0.02)
- **Timeline analytics** — your recent posts with full engagement metrics
- **Mentions** — who's replying to or quoting you, with their follower count
- **Bookmarks** — save, list, and manage your bookmarked posts
- **Follower tracking** — daily count with delta over time
- **Accountability** — tells you if you're spending too much time on X
- **Budget controls** — three modes (guarded / relaxed / unlimited), daily spend tracking, dry-run on every command
- **Smart caching** — every tweet is stored locally on first fetch and never re-fetched. Incremental pulls mean only new content costs money. This is how it stays at ~$1-2/mo instead of burning $25 on a single prompt

## Getting Started

```bash
git clone https://github.com/aaronnev/x-twitter-skill.git x-twitter
```

Then follow the **[Setup Guide →](SETUP.md)** — walks you through creating an X Developer account, getting your API keys, and configuring your budget. Takes about 10 minutes.

## How to Use

### Ask your agent

You don't need to memorise commands. Just talk to your AI agent naturally:

- *"What did my last 5 tweets do?"*
- *"Who mentioned me today?"*
- *"Read this thread: https://x.com/..."*
- *"Give me my morning X briefing"*
- *"How much have I spent on the API this week?"*
- *"Am I posting too much today?"*

Your agent reads [SKILL.md](SKILL.md) and picks the right script automatically.

### Budget controls

Three modes to control how much you spend:

- **Guarded** (default) — warns you and stops when you hit your daily limit
- **Relaxed** — warns you but keeps going
- **Unlimited** — no limits, no warnings

Every command also supports `--dry-run` to preview what it would cost before making any API calls.

## Commands

For terminal use or if you want to run scripts directly:

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

All commands support `--dry-run` (preview cost) and `--no-budget` (skip budget checks).

## Cost

X API v2 is pay-per-use. This skill keeps costs low:

| Usage | Daily | Monthly |
|-------|-------|---------|
| Morning briefing only | $0.02 | $0.60 |
| Briefing + a few checks | $0.04 | $1.20 |
| Heavy monitoring | $0.10 | $3.00 |

Cost scales with **check frequency**, not followers. 100 followers or 100K — same price.

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
