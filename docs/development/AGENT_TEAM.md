# Chronicle Agent Team v1

This document defines how Codex agents collaborate on Project Chronicle. The root
`AGENTS.md` remains the highest-priority project rule set. If this document conflicts
with it, the root rules win.

## Team structure

```text
User
  |
Primary Lead / Orchestrator
  |-- Builder
  |-- Reviewer
  |-- Researcher
  `-- Peer Lead / Architecture Auditor, when justified
        `-- Astra specialist, only for the hardest cases
```

The Primary Lead manages delegation, result collection, revision requests, and
re-review. The user must not become the messenger between agents. The Lead reports
only the conclusions and evidence the user needs.

## Primary Lead / Orchestrator

The default operating model is **GPT-5.6 Sol High**, when it is available in the
current Codex environment.

The Lead:

- determines the goal, scope, difficulty, and risk;
- asks whether another agent would materially improve quality or safety;
- selects the smallest sufficient team and passes only the necessary context;
- integrates agent results and resolves revision cycles;
- chooses the appropriate test scope;
- checks the repository state before integration; and
- stops at a user decision or approval gate when one is actually required.

The Lead handles small, safe tasks directly.

## Agent creation and usage budget

Before creating an agent, the Lead asks:

> Would quality or safety actually decrease without this agent?

If the answer is no, the agent is not created. The default configuration is the
Lead alone or the Lead plus one execution agent. When both a Builder and Reviewer
are justified, they should normally run sequentially. Avoid habitual fan-out,
repeated broad repository analysis, and multiple agents reading the same files.

The user uses ChatGPT Plus and wants the weekly Codex quota to last without extra
spending. The Lead must not assume that it knows the current quota. If the user
provides the recent weekly remaining percentage, use it as follows:

| Weekly remaining | Operating guide |
| --- | --- |
| 60% or more | Normal minimal-agent operation |
| 30-60% | Minimize Astra; normally keep to Lead plus one agent |
| 15-30% | Prioritize important implementation; use Peer Lead or Reviewer only for high-risk changes |
| Below 15% | Avoid fan-out; do not invoke Astra automatically; ask the user before an essential Astra escalation |

When the quota is unknown, operate conservatively. If agent fan-out has low value
for its usage cost, stop expanding the team and choose the smallest safe next step.

## Roles

### Builder

- Implements only the assigned scope and avoids unrelated refactoring.
- Runs the smallest focused tests needed for the changed behavior.
- Uses an isolated worktree when concurrent or isolated code changes require it.
- Reports changed files, verification results, and unresolved risks to the Lead.

### Reviewer

- Reviews the Builder's exact diff and relevant test evidence.
- Checks regression, security, race conditions, lifecycle behavior, and architecture
  invariants when applicable.
- Works read-only by default and requests corrections through the Lead.
- Focuses on whether the implementation correctly realizes the chosen design.

### Researcher

- Is created only when current external API or official documentation is necessary.
- Does not implement code.
- Returns official sources, verified facts, constraints, and remaining uncertainty.

### Peer Lead / Architecture Auditor

- Independently reviews whether the Primary Lead chose the right direction.
- May disagree with the Primary Lead and propose a different architecture.
- Is not a standing participant and does not replace an implementation Reviewer.

Consider a Peer Lead only for:

- a new core architecture decision;
- database schema or migration work with data-loss risk;
- difficult async, concurrency, or race-condition design;
- retry, fallback, or routing across several subsystems;
- authentication, authorization, or security design;
- a large refactor;
- two similarly credible designs the Lead cannot resolve; or
- a Reviewer objection to the design itself rather than its implementation.

Do not use a Peer Lead for ordinary CRUD, small provider changes, documentation,
smoke tests, or other routine work.

## Model routing

Use the least expensive model that can safely complete the role:

- Primary Lead: GPT-5.6 Sol High by default.
- Simple execution, Git operations, and small checks: a lighter available model.
- General implementation: a mid-tier model.
- Complex implementation or review: a Sol-level model.
- GPT-6 Astra: a specialist for the hardest architecture, race, migration, data-loss,
  or multi-subsystem integration decisions.

Do not spend Astra on `git status`, commit or push operations, API smoke tests,
documentation, simple tests, ordinary CRUD, or small implementation with an agreed
design. Use at most one Astra specialist per task by default. Before invoking it,
the Lead defines why the current model is insufficient, the exact question to
resolve, and the minimum context required.

## Git, worktrees, and forks

Multiple writing agents must not modify the same `main` working tree concurrently.
When isolation is needed, a code implementation agent works in a dedicated worktree
and a Reviewer reads that worktree or diff. The Lead verifies the reviewed result
before integration. Agents do not have to commit independently.

Commit and push require the user's explicit instruction under the root `AGENTS.md`.
Multiple agents must not modify real SQLite production or development data in
parallel.

Forks and worktrees serve different purposes:

- Use a **fork** to compare two independently credible designs or hypotheses from
  the same starting point, such as architecture A/B or migration strategy A/B.
- Use a **worktree** to isolate an actual code-change workspace.

Continue the durable Lead thread for an ordinary next step. Do not create habitual
forks because they consume additional quota.

## User decision and approval gates

Stop for user approval or a product decision when required for:

- a destructive migration or meaningful data-loss risk;
- a major architecture direction change;
- an external API operation that may create meaningful cost;
- a product or business policy choice;
- competing large designs with similar merit; or
- a requested commit or push.

Existing user authorization in the current task still applies. Routine work within
the approved scope should proceed through planning, implementation, focused testing,
review, revision, and verification without making the user relay agent messages.

## Testing policy

Run tests in stages:

```text
focused test -> related regression tests -> full suite only when justified
```

Do not have several agents repeat the same full test suite. The Lead decides when
broader verification adds enough value.
