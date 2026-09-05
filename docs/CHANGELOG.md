# Changelog

## Unreleased

### Stabilization

- Clarified that `CollectionChannel` selects analysis targets and does not control whether guild messages are collected.
- Added repository-level agent rules documenting raw-data preservation, soft-delete, layering, scope, and time contracts.
- Added atomic message soft delete with deletion history and a safe Alembic migration for nullable `messages.deleted_at`.
- Normalized UTC storage and query behavior while interpreting analysis inputs and presenting statistics in KST.
- Stabilized `ConversationBuffer` timeout, cleanup, flush, and shutdown lifecycle behavior.
- Made message creation idempotent across duplicate Discord create events, preserving original content and avoiding duplicate conversation buffering.
- Declared the `fasttext-langdetect` dependency used by the language detection path.
