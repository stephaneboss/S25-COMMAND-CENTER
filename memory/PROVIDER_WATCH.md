# Provider Watch Snapshot

- Generated at: `2026-03-10T17:06:18.172103+00:00`
- Global status: `partial`

## Current official-source checks

### OpenAI

- `changelog` [Changelog | OpenAI API](https://platform.openai.com/docs/changelog) [ok]
  S25 note: Track Responses API, tools, MCP, background mode, and GPT-compatible patterns.
- `responses_news` [New tools and features in the Responses API](https://openai.com/index/new-tools-and-features-in-the-responses-api/) [ok]
  S25 note: Use as product direction for agent tooling and future TRINITY upgrades.

### Google

- `gemini_changelog` [Release notes  |  Gemini API  |  Google AI for Developers](https://ai.google.dev/gemini-api/docs/changelog) [ok]
  S25 note: Gemini remains the long-term memory and retrieval pillar for S25.
- `embedding_ga` [Gemini Embedding now generally available in the Gemini API- Google Developers Blog](https://developers.googleblog.com/en/gemini-embedding-available-gemini-api/) [ok]
  S25 note: Watch embedding updates and retirement windows for legacy embedding models.

### Anthropic

- `release_notes` [Claude Developer Platform](https://docs.anthropic.com/en/release-notes/api) [ok]
  S25 note: Watch compatibility features, model lifecycle, and code/backend primitives.

### Perplexity

- `comet_shortcuts` [comet_shortcuts](https://www.perplexity.ai/help-center/en/articles/11897890-comet-shortcuts) [restricted]
  S25 note: Shortcuts are the best current lever for repeatable provider-watch workflows in Comet.
- `assistant_permissions` [assistant_permissions](https://comet-help.perplexity.ai/en/articles/12658082-control-what-comet-assistant-can-use) [restricted]
  S25 note: Use to keep Comet useful but constrained when it touches account surfaces.
- `work_guide` [work_guide_pdf](https://r2cdn.perplexity.ai/pdf/pplx-at-work.pdf) [ok]
  S25 note: Use Work patterns to turn provider watch into a repeatable operating routine.

## Use in S25

- Feed this snapshot to TRINITY, MERLIN, or COMET when reviewing provider changes.
- Treat Google/Gemini as the long-term memory and retrieval base.
- Treat OpenAI/TRINITY as the orchestration surface for voice and action flows.
- Treat Claude/Codex as the backend implementation force.
- Treat Comet as the browser-native watchtower for product, work, and workflow updates.
