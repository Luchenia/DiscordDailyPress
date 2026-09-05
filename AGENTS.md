# Project Chronicle Core Rules

- This project is Project Chronicle / DiscordDailyPress, an AI newspaper system for Discord.
- Preserve raw collected Discord data as the source of truth; derived processing must not destructively overwrite it.
- Keep collection and analysis separate. `CollectionChannel` identifies an analysis target, not collection permission; messages may be collected broadly, while channel activation controls analysis inclusion.
- Discord message deletion must be soft delete: preserve the original message row/content and record deletion history.
- Store and compare database timestamps in UTC. Interpret and display user-facing periods, statistics, dates, and times in KST unless explicitly specified otherwise.
- Preserve the layered architecture: Collector -> DTO/Domain -> Service -> Repository -> SQLite.
- Put business logic in Service/domain code rather than Discord command handlers when practical.
- Do not overwrite `messages.content` with translations. Raw message content must remain immutable with respect to translation and other derived processing.
- Avoid blocking the Discord event loop with synchronous network or heavy processing.
- Keep changes narrowly scoped; do not perform unrelated refactors.
- Read only files needed for the current task; do not repeatedly scan the entire repository.
- Run focused tests for changed behavior first, and the full suite only when appropriate for final verification.
- Do not commit or push unless explicitly instructed.
- Never delete or rewrite existing user data during schema migrations unless explicitly instructed. Verify assumptions about existing data before migrating or converting it.
