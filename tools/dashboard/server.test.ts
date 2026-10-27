import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { buildRows, loadSessions, render, type Pr, type Session } from "./server.ts";

const now = Date.parse("2026-10-27T12:00:00Z");
const DAY = 86_400_000;

const session = (over: Partial<Session>): Session => ({ id: "local_x", title: "S", project: "p", lastActivity: now, running: false, prs: [], ...over });
const pr = (over: Partial<Pr>): Pr => ({ repo: "o/r", number: 1, title: "PR", url: "https://x/1", state: "OPEN", updatedAt: now, isDraft: false, reviewRequested: false, ...over });

test("buckets sessions and PRs", () => {
  const rows = buildRows(
    [
      session({ id: "a", needsUser: "Sign in to Maxio" }),
      session({ id: "b", running: true }),
      session({ id: "c", prs: [{ repo: "o/r", number: 1, url: "u", state: "OPEN" }] }),
      session({ id: "d", prs: [{ repo: "o/r", number: 2, url: "u", state: "MERGED" }], lastActivity: now - 30 * DAY }),
      session({ id: "e", lastActivity: now - 10 * DAY }),
    ],
    [pr({ number: 1, ci: "FAILURE" }), pr({ number: 3, reviewRequested: true }), pr({ number: 4, isDraft: true })],
    now,
  );
  const by = (id: string) => rows.find((r) => r.session?.id === id || (!r.session && r.prs[0].number === Number(id)))!;
  assert.equal(by("a").bucket, "needs");
  assert.equal(by("b").bucket, "running");
  assert.deepEqual([by("c").bucket, by("c").reason], ["needs", "CI failing"]);
  assert.deepEqual([by("d").bucket, by("d").reason], ["done", "Merged, archive me"]);
  assert.deepEqual([by("e").bucket, by("e").stale], ["idle", true]);
  assert.deepEqual([by("3").bucket, by("3").reason], ["needs", "Your review is requested"]);
  assert.equal(by("4").bucket, "idle");
  assert.equal(rows.length, 7); // PR #1 joins session c instead of getting its own row
});

test("reads session files, skips archived and malformed ones", () => {
  const dir = mkdtempSync(join(tmpdir(), "dash-"));
  mkdirSync(join(dir, "acct/org"), { recursive: true });
  const w = (name: string, d: unknown) => writeFileSync(join(dir, "acct/org", name), JSON.stringify(d));
  w("local_1.json", { sessionId: "local_1", title: "Live", cwd: "/x/copa.fyi/.claude/worktrees/abc", lastActivityAt: now, latestUserFrameAt: now, lastTurnEdgeAt: now - 1, turnWrapUp: { needsUser: "Q?" }, prs: [{ repo: "o/r", prNumber: 5, url: "u", state: "OPEN" }] });
  w("local_2.json", { sessionId: "local_2", title: "Old", isArchived: true });
  w("local_3.json", { nope: true });
  w("local_4.json", { sessionId: "local_4", title: "Pre-field", lastActivityAt: now, latestUserFrameAt: now });
  w("local_5.json", { sessionId: "local_5", title: "Killed", lastActivityAt: now - DAY, latestUserFrameAt: now - DAY, lastTurnEdgeAt: now - 2 * DAY });
  const { sessions, warnings } = loadSessions(dir, now);
  assert.equal(sessions.length, 3);
  const live = sessions.find((s) => s.id === "local_1")!;
  assert.deepEqual([live.project, live.running, live.needsUser, live.prs[0].number], ["copa.fyi", true, "Q?", 5]);
  assert.ok(sessions.filter((s) => s.id !== "local_1").every((s) => !s.running));
  assert.equal(warnings.length, 1);
});

test("render escapes titles", () => {
  const html = render(buildRows([session({ title: "<script>" })], [], now), [], now);
  assert.ok(html.includes("&#60;script&#62;") && !html.includes("<script>"));
});
