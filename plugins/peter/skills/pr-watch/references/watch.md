# Persistent watch

## Scope and private state

Find an existing matching automation and its saved state before starting anything. In Codex use the automation tool and inspect matching automation configuration when needed. Search the current chat and project context for prior scope. Reuse it unless the user changes it. A resumed watch must preserve previous review URLs and findings.

For a new scope, inspect the app's registered projects, trusted project context and Git remotes. Deduplicate repositories by owner/name. Include known active mirrors as separate PR destinations. Prefer explicit active-project evidence over every repository the account can access. Connector inventories can omit private repositories: use authenticated `gh` to verify known remotes. Resolve genuinely ambiguous PR numbers before posting. Record excluded or inaccessible repositories and surface failures; never silently treat a failed lookup as an empty repository.

Keep configuration under the current workspace's `work/`, for example `work/pr-monitor-state.json`. Persist repository additions when the user identifies another current project; refresh discovery on start/resume and when the active project list changes. Do not put personal repository lists or machine paths into this public skill.

Minimum initial state:

```json
{"schemaVersion":1,"scope":["owner/repo"],"prs":{},"automation":{"intervalMinutes":5}}
```

Each PR record distinguishes observed `headSha`/`baseSha` from `reviewedHeadSha`/`reviewedBaseSha`; retain actual `baseRef`, state/draft status, checks, discussion/review IDs, review threads, review URLs, verified findings and validation limits. When migrating older state, derive a missing reviewed base only from the saved review evidence; otherwise inspect the current diff before claiming coverage. Preserve prior closed/merged records so interrupted work and publication history remain recoverable. Record the last notified outcome to suppress repeat notifications.

## Scheduler lifecycle

Use the native scheduler supported by the host. In Codex, discover `automation_update` and use a **thread heartbeat**, local to the current chat, with a five-minute interval and ACTIVE status. Reuse a matching watch rather than creating a second one. Preserve unrelated fields when updating. Do not simulate persistence with a shell loop, repeated sleeps or a standalone cron job. If no supported scheduler is available, finish the immediate review and report that recurring checks were not enabled.

The saved prompt must be self-contained: reference this skill's installed path, the absolute private state path, its scope, interval, review/publishing authorization, and the instruction to continue until stopped. Include quiet notifications, no overlapping cycles, no duplicate comments, and no code/merge/deploy actions. A heartbeat should resume pending work before launching another pass. Keep one coordinator; child agents are internal workers, not new sidebar chats. Bound concurrency by available agent slots. Do not send prompts to unrelated existing user chats.

On stop, first deactivate the matching automation, then mark the watch stopped and interrupt its active workers. Check for a stop message before each publication. Do not publish returned work after a stop. Read the scheduler result to verify deactivation; report any failure. Resume only when requested. Status requests are read-only.

## Poll, review, acknowledge

Use connector calls when sufficient. The packaged helper is the CLI fallback:

```bash
python3 <skill-dir>/scripts/poll.py --state <absolute-state-path>
```

Read its JSON result and snapshot. It performs no GitHub writes. Consult `--help` for snapshot options. It does not acknowledge changed heads or replace code review. Serialize cycles in the coordinator; do not run two polls against the same state concurrently.

1. Inventory **all** open PRs in scope, including drafts and newly opened PRs. Fetch previously open PRs that disappear to distinguish merged/closed from failed inventory. Read current statuses even for unchanged heads. Never silently truncate pagination.
2. For new/changed heads, review new commits plus relevant surrounding code and verify previous findings. A changed base can change the effective diff without a new head, so assess that delta too. For discussion-only changes, inspect the new evidence. Do not rerun reviews/tests merely because a bot edited a preview comment.
3. After review, recheck live head and discussions before publishing. If the head moved, review its delta first. Before a write, persist `pendingPublication` with the target head/base, intended review content fingerprint and attempt time. An uncertain GitHub write requires inspecting existing reviews for matching commit/content before retrying. Save the resulting review ID/URL and exact reviewed head/base only after the corresponding review completes, then clear the pending record. Private reviews save a completed private result instead of a GitHub ID.
4. Merge the completed snapshot into state atomically, retaining review evidence and unresolved work. Advance observed status/discussion baselines after handling them. Never set `reviewedHeadSha` from an inventory result. If review or publishing fails, leave that work pending. On partial API failure preserve the last complete baseline and retry later; notify about the failure once and about recovery when meaningful.

Head and CI changes are separate. Distinguish tests executed by reviewers from GitHub CI. Suppress transient UNKNOWN mergeability, check reordering, deployment URL changes and already acknowledged discussions unless they change a user decision. Notify once about new actionable failures, verified recovery, merge/closure, verified fixes, or new findings. A clean summary on GitHub belongs to a newly reviewed head or materially changed diff, never every poll. Do not report an indefinitely continuing watch as finished just because the current queue is empty.
