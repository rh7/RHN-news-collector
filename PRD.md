## Personal News Intelligence System – PRD (Collector Service)

### Goals
- Build a reliable, extensible news collection service that fetches content from multiple sources (starting with Readwise Reader) and stores normalized articles in Supabase.
- Operate as an independent service with its own deployment cycle and database write access.

### Non-Goals
- No analysis, summarization, or delivery (handled by the separate intelligence service).

### Architecture
- Service: `news-collector` (Python)
- Communication: Supabase PostgreSQL only
- Deploy target: Vercel (serverless functions) and local CLI runner
- Storage tables used: `sources`, `contents`

### Key Components
- `core/db_client.py`: Supabase wrapper for write operations
- `collectors/base.py`: Abstract collector interface and `Article` dataclass
- `collectors/readwise.py`: Readwise Reader implementation (phase 1)
- `core/collector_manager.py`: Orchestrates collectors, persists results, updates sync metadata
- `api/*.py`: Vercel endpoints for scheduled and manual triggers
- `scripts/*.py`: Setup helpers (e.g., initialize sources)

### Data Contracts
- `Article` normalized fields: `external_id`, `title`, `url`, `content`, `author`, `published_at`, `metadata`
- `contents` uniqueness: `(source_id, external_id)`

### Source Plugin Contract
- `validate_config()` must ensure required credentials are present.
- `test_connection()` should try a quick network check and return boolean.
- `collect()` returns `(List[Article], updated_sync_metadata: Dict)` and should support incremental sync.

### Coding & Organization
- Max file length: 500 LoC; split into modules if approaching the limit.
- Clear module separation by responsibility; prefer explicit imports within repository packages.
- Add concise comments for non-obvious logic with a `# Reason:` note when appropriate.

### Observability
- Structured logging with counts per source, errors collected per run.

### Constraints
- Vercel function timeout defaults to 60s — stay within limits; pagination and safety caps included.
- Handle API/network errors gracefully; partial success preferred over all-or-nothing.

### Future Extensions
- Additional collectors: RSS, Hacker News, Reddit, Twitter
- Rate limit/backoff utilities; shared HTTP client
- Web UI to manage source configs


