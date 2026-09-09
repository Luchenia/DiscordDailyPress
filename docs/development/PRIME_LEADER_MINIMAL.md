# Prime Leader Minimal Connection Proof

## Status and purpose

This document defines the smallest manual connection proof for Prime Leader work.
It records a bounded operating procedure; it does not claim unattended automation,
a running orchestration service, or a completed end-to-end proof.

Invocation is manual over the existing `chronicle-dev` SSH connection. The operator
selects the existing session for the intended repository and supplies an approved,
bounded task:

- Chronicle Development session:
  `01a08084-1ea3-7430-b459-468b7a76087d`, in
  `/home/amadeus/projects/DiscordDailyPress`.
- Marketing session: `01a07c96-4013-7600-9999-8b0921e04cb0`, in the separate
  `/home/amadeus/marketing-capture` workspace, which uses sidecar Git.

The sessions and workspaces must not be substituted for each other. Marketing
v0.3-alpha remains frozen, and its `.git` placeholder must remain untouched.

## Preflight

Before reading or changing task files, Prime verifies the active working directory,
Git top-level directory, branch, working-tree status, HEAD, and configured remote
against the task's expected values. It also reads the repository-local `AGENTS.md`
and any instructions it references.

Prime proceeds only when the complete preflight matches. An absent or unusable Git
directory, an unexpected branch, commit, remote, dirty file, workspace, session, or
instruction is an unexpected repository state and triggers fail-closed behavior.

## Bounded delegation

Within a Founder-approved task, Prime is delegated authority to perform routine
repository reads, focused and required regression tests, explicit-path staging,
validated normal commits, and verified fast-forward pushes to the known remote when
the approved task includes that push. Prime keeps the file list, command scope,
repository, branch, commit message, and remote within the stated task boundary.

Founder approval remains required before sudo; system, network, or permission
changes outside an already approved operation; access to or modification of
credentials, secrets, or security controls; destructive data or destructive Git
operations; spending or paid API use; public SNS publication; major product or
architecture decisions; and any action after unexpected repository state is found.
The delegation in this document does not widen an individual task's authorization.

## Independent diff validation

Prime validates the change independently before staging:

1. Compare `git status --short` with the approved path list.
2. Inspect the complete diff and confirm it implements only the bounded task.
3. Check for database, migration, schema, environment, secret, credential, runtime,
   generated, and unrelated files.
4. Run the task's focused checks first and broader tests only when required.
5. Run `git diff --check` and resolve only commit-blocking issues inside scope.
6. Stage approved files with explicit paths; never use broad staging as a shortcut.
7. Compare the staged path list with the approved list and confirm no relevant
   unstaged change remains.

Validation performed by the implementation session is evidence, but Prime still
checks the actual working tree and staged diff before committing.

## Commit and remote verification

For an approved normal commit, Prime verifies the staged file list and commit
message immediately before committing. Afterward it records the full commit hash,
shows branch status and the committed file/stat summary, and confirms whether the
working tree is clean.

For an approved known-remote push, Prime first verifies the exact local HEAD, a clean
working tree, the expected branch, the configured remote URL, and the expected
ahead/behind relationship. It uses a normal fast-forward push and never forces the
remote. After the push it verifies that local HEAD and the remote-tracking branch
resolve to the same full hash and reports `git status --short --branch`.

## Fail-closed behavior

Prime stops before the affected action and reports the observed mismatch when a
preflight, diff, test, staged-file, commit, or remote check differs from the approved
expectation. Prime does not repair repository metadata, change remotes, broaden the
file set, bypass checks, force a Git operation, contact another workspace, or infer
approval from earlier unrelated work.

The Founder decides how to proceed after an unexpected state or approval-gated
operation. Until then, Prime leaves repository data, services, runtime state,
credentials, the Marketing v0.3-alpha release, and its `.git` placeholder unchanged.
