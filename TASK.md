## Task Log

Date: 2025-09-28

### Open Tasks
- [ ] Create project scaffolding and configuration files
- [ ] Implement Supabase database client wrapper
- [ ] Implement base collector and Readwise collector
- [ ] Implement collector manager orchestrating all sources
- [ ] Implement Vercel API endpoints (collect, collect_readwise, health)
- [ ] Add scripts (setup_sources, test_collector)
- [ ] Add tests and placeholders for other collectors
- [ ] Update README with setup, local run, and deployment steps

### Discovered During Work
- [ ] Ensure imports avoid fragile relative paths; use package-style imports (`collectors.*`, `core.*`).
- [x] Readwise: request full HTML via `withHtmlContent=true` and use `updatedAfter` for incremental sync (2025-09-28)
- [x] Switch Reader source to `location=feed`, fetch up to 100 items/hour, dedupe via upsert (2025-09-28)


