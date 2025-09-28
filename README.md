## News Collector

Python service that collects articles from configured sources (starting with Readwise Reader) and stores them in Supabase for downstream analysis.

### Features
- Pluggable collectors with a common `Article` schema
- Incremental sync via `sync_metadata` on sources
- Vercel endpoints for scheduled/manual runs

### Quick Start
1. Create a Supabase project and apply the provided SQL schema (see PRD).
2. Copy `.env.example` to `.env` and fill values.
3. Install deps:
   ```bash
   pip install -r requirements.txt
   ```
4. Initialize sources:
   ```bash
   python scripts/setup_sources.py
   ```
5. Run locally:
   ```bash
   python main.py
   ```

### Endpoints (Vercel)
- `api/health.py` — health check
- `api/collect.py` — scheduled collection (all enabled sources)
- `api/collect_readwise.py` — manual Readwise-only trigger

### Environment
See `.env.example` for required variables.

#### Readwise Reader
- Set `READWISE_TOKEN` in your environment. The Readwise collector requests full article HTML using `withHtmlContent=true` and performs incremental syncs using `updatedAfter` based on the source's `sync_metadata.last_sync_date`.

#### Feed collection (Reader)
- Default source is the Reader Feed (`location: feed`).
- The collector fetches up to `max_items` per run (default `100`).
- Configure via environment:
  - `READWISE_TOKEN` — required
  - `READER_FEED_MAX_ITEMS` — optional, defaults to `100`
- De-duplication is enforced at write time using `contents` unique key `(source_id, external_id)` with upserts.

### Scheduling
- Vercel cron is configured to run hourly.
  - See `vercel.json` → `crons: [{ path: "/api/collect", schedule: "0 * * * *" }]`.



### Hacker News configuration
- **HN_LIST**: which list to fetch (`new`, `top`, or `best`). Default: `top`.
- **HN_MAX_ITEMS**: max number of stories per run. Default: `50`.

Add these to your `.env`:
```env
# Hacker News
HN_LIST=top
HN_MAX_ITEMS=50
```


