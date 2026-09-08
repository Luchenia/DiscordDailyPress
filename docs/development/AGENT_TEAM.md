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

The normal Development Primary Lead is **GPT-5.6 Sol** with **High reasoning
effort** and **fast mode off**, when that routing is available in the current Codex
environment.

Sol High is preferred for ordinary feature implementation, DTO / Service /
Repository work, routine architecture decisions, tests and regression validation,
documentation, normal bug fixes, bounded refactors, and routine Git development
workflow. Do not escalate merely because a task is large. Escalation follows
reasoning difficulty and risk, not task length or prestige.

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
Primary Lead alone. Use at most one additional active Builder or Reviewer when that
agent is genuinely useful. When both are useful, prefer using them sequentially.
Avoid habitual fan-out, repeated broad repository analysis, and multiple agents
reading the same files. Researcher is used only when current official documentation
or external factual verification is actually required.

Use the least expensive model that can complete the current work safely and with
high confidence. Do not sacrifice correctness, architecture safety, or data
integrity to save quota, and do not spend Astra quota where Sol High is clearly
sufficient. The priority is correctness, then appropriate reasoning capability,
then quota efficiency. Do not assume that current token usage, quota, or cost is
known.

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

Consider a Peer Lead or architecture-focused Reviewer only for:

- a new core architecture decision;
- database schema or migration work with data-loss risk;
- difficult async, concurrency, or race-condition design;
- retry, fallback, or routing across several subsystems;
- authentication, authorization, or security design;
- two similarly credible designs the Lead cannot resolve; or
- a Reviewer objection to the design itself rather than its implementation.

Do not use a Peer Lead for ordinary CRUD, small provider changes, documentation,
smoke tests, or other routine work.

## Model routing and Astra escalation

Astra may be selected when the **current** problem materially benefits from higher
reasoning capability. Typical cases include:

- difficult or unresolved architecture conflicts;
- concurrency, race-condition, async lifecycle, or ordering problems;
- destructive migration or meaningful data-loss risk;
- security-sensitive architecture;
- subtle source-of-truth or derived-data integrity conflicts;
- difficult multi-subsystem interactions;
- hard correctness bugs that Sol High has investigated but cannot resolve
  confidently; or
- decisions where a wrong architecture choice would create substantial future
  rework.

Astra does not require separate user approval merely because Astra is being used.
It may autonomously investigate, review, and arbitrate difficult architecture
questions. It must not be selected simply because it is the stronger model.

Do not treat Astra as a one-question-only specialist. Astra may remain the Primary
Lead while the remaining task continues to require Astra-level reasoning, including
continued architecture arbitration, related race-condition fixes, tightly coupled
migration design and implementation, or continuing security and integrity work.
When the difficult decision is resolved and the remaining work is routine, prefer
returning to Sol High for straightforward implementation, repetitive tests, normal
documentation, mechanical refactoring, routine Git operations, and simple follow-up
fixes. Model allocation is fluid and based on the current work.

Astra may instead serve as a narrow specialist when the overall task is Sol-level
but one isolated architecture, security, concurrency, migration, or integrity
question is Astra-level:

```text
Sol High Primary Lead
  -> Astra reviews the narrow difficult question
  -> conclusion returns to the Primary Lead
  -> normal implementation continues at the appropriate model level
```

If that review shows the whole remaining task is Astra-level, Astra may remain
involved or become the Primary Lead when the environment supports that workflow.

## Factual model reporting

Never guess or invent runtime model information. Distinguish requested, observable,
and inferred model information, and never present an inference as measured fact. Do
not claim that Sol High, Astra, or another model was used unless it is observable or
otherwise verifiable. When runtime telemetry is unavailable, report:

> Actual runtime model/effort telemetry was not verifiable.

At the end of a substantial development task, use this format:

```text
역할 / 실제 확인 가능한 모델·effort / 투입 목적 / 결과·검증
추가 Agent 수 / N
Astra specialist 수 / N
```

If a verifiable model change occurred, also report the previous model, new model,
reason for escalation or downgrade, and whether the higher-capability model remained
necessary afterward. Report token usage, quota consumption, or cost only when it is
actually measurable; never present estimates as telemetry.

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

Model escalation does not grant additional operational authority. Regardless of
model, stop and request user approval before:

- destructive migrations;
- data deletion or irreversible data transformation;
- meaningful-cost external API calls;
- sudo, system, OS, network, credential, or security changes;
- implementing a major architecture direction change or materially changing an
  established subsystem boundary or invariant;
- choosing between two large competing architectures that remain similarly credible
  when the choice would create substantial long-term lock-in or rework;
- unresolved product or business decisions with meaningful consequences;
- Git commit; or
- Git push.

In the competing-architecture case, surface the decision to the user before
implementation.

Existing user authorization in the current task still applies. Routine work within
the approved scope should proceed through planning, implementation, focused testing,
review, revision, and verification without making the user relay agent messages.

## Chronicle invariants

No model, including Astra, may override established Chronicle invariants without
explicit user approval:

- Raw collected Discord data remains the long-lived source of truth.
- Derived data remains regenerable.
- `CollectionChannel` controls analysis scope, not collection permission.
- Discord deletion follows the existing soft-delete policy.
- Translations never overwrite `messages.content`.
- Database timestamps remain UTC; user-facing analysis and display follow the
  established timezone policy.
- Collection and analysis remain separate.
- External or blocking work must not be introduced into the Discord event loop.
- Unrelated refactors are avoided.
- Ordinary tests must not mutate the production database.

If a proposed implementation conflicts with an invariant, stop and surface the
conflict rather than silently changing the invariant.

## Testing policy

Run tests in stages:

```text
focused test -> related regression tests -> full suite only when justified
```

Do not have several agents repeat the same full test suite. The Lead decides when
broader verification adds enough value.

## Decision rule

For every substantial task, reason internally using this hierarchy:

1. Can Sol High solve the current work safely and confidently?
   - Yes: use or retain Sol High.
2. Is there a genuine high-complexity or high-risk reasoning problem?
   - Yes: Astra may be used.
3. After escalation, is the remaining task still Astra-level?
   - Yes: Astra may remain.
   - No: prefer returning to Sol High.

Do not optimize for model prestige. Optimize for project correctness, development
speed, and sustainable quota usage.
