// Local read-only dashboard of Claude Code sessions and GitHub PRs.
// Run: node tools/dashboard/server.ts   then open http://localhost:4400
import { execFile } from "node:child_process";
import { readdirSync, readFileSync } from "node:fs";
import { createServer } from "node:http";
import { homedir } from "node:os";
import { basename, join } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const PORT = Number(process.env.PORT ?? 4400);
// The desktop app's private session store; undocumented, so every field is read defensively.
const SESSIONS_DIR = join(homedir(), "Library/Application Support/Claude/claude-code-sessions");
const DAY = 86_400_000;
const STALE_DAYS = 7;
const DONE_DAYS = 3;

type SessionPr = { repo: string; number: number; url: string; state: string };
export type Session = {
  id: string;
  title: string;
  project: string;
  lastActivity: number;
  running: boolean;
  needsUser?: string;
  recap?: string;
  prs: SessionPr[];
};
export type Pr = {
  repo: string;
  number: number;
  title: string;
  url: string;
  state: string; // OPEN | MERGED | CLOSED
  updatedAt: number;
  mergedAt?: number;
  isDraft: boolean;
  ci?: string; // statusCheckRollup state: SUCCESS | FAILURE | ERROR | PENDING | EXPECTED
  review?: string; // APPROVED | CHANGES_REQUESTED | REVIEW_REQUIRED
  reviewRequested: boolean; // someone asked for my review
};
export type Bucket = "needs" | "running" | "idle" | "done";
export type Row = { bucket: Bucket; reason: string; stale: boolean; age: number; session?: Session; prs: Pr[]; title: string; project: string };

const time = (v: unknown) => (typeof v === "number" || typeof v === "string" ? new Date(v).getTime() || 0 : 0);

function projectOf(cwd: string) {
  return basename(cwd.split("/.claude/worktrees/")[0] ?? cwd);
}

export function loadSessions(dir = SESSIONS_DIR, now = Date.now()): { sessions: Session[]; warnings: string[] } {
  const sessions: Session[] = [];
  const warnings: string[] = [];
  let files: string[];
  try {
    files = readdirSync(dir, { recursive: true, encoding: "utf8" }).filter((f) => /(^|\/)local_[^/]+\.json$/.test(f));
  } catch (e) {
    return { sessions, warnings: [`Can't read ${dir}: ${(e as Error).message}`] };
  }
  let malformed = 0;
  for (const f of files) {
    let d: any;
    try {
      d = JSON.parse(readFileSync(join(dir, f), "utf8"));
    } catch {
      malformed++;
      continue;
    }
    if (typeof d?.sessionId !== "string" || typeof d?.title !== "string") {
      malformed++;
      continue;
    }
    if (d.isArchived) continue;
    const wrap = d.turnWrapUp ?? {};
    const str = (v: unknown) => (typeof v === "string" ? v : undefined);
    const lastActivity = time(d.lastActivityAt);
    sessions.push({
      id: d.sessionId,
      title: d.title,
      project: projectOf(String(d.cwd ?? "")),
      lastActivity,
      // Mid-turn: the latest user message is newer than the last turn end. Older sessions lack
      // lastTurnEdgeAt, and a turn silent for 30 min was most likely killed, not still working.
      running: !!d.lastTurnEdgeAt && time(d.latestUserFrameAt) > time(d.lastTurnEdgeAt) && now - lastActivity < 30 * 60_000,
      needsUser: str(wrap.needsUser) ?? (d.interruptedAwaitingPerson ? "Interrupted, waiting for you" : undefined),
      recap: str(wrap.description),
      prs: (Array.isArray(d.prs) ? d.prs : [])
        .filter((p: any) => typeof p?.repo === "string" && typeof p?.prNumber === "number")
        .map((p: any) => ({ repo: p.repo, number: p.prNumber, url: String(p.url ?? ""), state: String(p.state ?? "") })),
    });
  }
  if (malformed) warnings.push(`${malformed} session file(s) had an unexpected shape and were skipped. The app's format may have changed.`);
  return { sessions, warnings };
}

const run = promisify(execFile);
const PR_FIELDS = `... on PullRequest { number title url state updatedAt mergedAt isDraft reviewDecision
  repository { nameWithOwner } commits(last: 1) { nodes { commit { statusCheckRollup { state } } } } }`;

async function search(q: string): Promise<any[]> {
  // shortcut: first 100 results only, no pagination; fine for one person's PRs.
  const query = `query($q: String!) { search(query: $q, type: ISSUE, first: 100) { nodes { ${PR_FIELDS} } } }`;
  const { stdout } = await run("gh", ["api", "graphql", "-f", `query=${query}`, "-f", `q=${q}`], { maxBuffer: 20e6 });
  return JSON.parse(stdout).data.search.nodes;
}

export async function loadPrs(now = Date.now()): Promise<{ prs: Pr[]; warnings: string[] }> {
  const since = new Date(now - DONE_DAYS * DAY).toISOString().slice(0, 10);
  try {
    const [mine, asked, merged] = await Promise.all([
      search("is:pr is:open author:@me archived:false"),
      search("is:pr is:open review-requested:@me archived:false"),
      search(`is:pr is:merged author:@me merged:>=${since}`),
    ]);
    const byKey = new Map<string, Pr>();
    for (const [list, reviewRequested] of [[mine, false], [merged, false], [asked, true]] as const) {
      for (const n of list) {
        const pr: Pr = {
          repo: n.repository.nameWithOwner,
          number: n.number,
          title: n.title,
          url: n.url,
          state: n.state,
          updatedAt: time(n.updatedAt),
          mergedAt: n.mergedAt ? time(n.mergedAt) : undefined,
          isDraft: n.isDraft,
          ci: n.commits?.nodes?.[0]?.commit?.statusCheckRollup?.state ?? undefined,
          review: n.reviewDecision ?? undefined,
          reviewRequested,
        };
        byKey.set(`${pr.repo}#${pr.number}`, pr);
      }
    }
    return { prs: [...byKey.values()], warnings: [] };
  } catch (e) {
    return { prs: [], warnings: [`GitHub lookup failed (is gh logged in?): ${(e as Error).message.split("\n")[0]}`] };
  }
}

function prNeeds(pr: Pr): string | undefined {
  if (pr.state !== "OPEN") return;
  if (pr.reviewRequested) return "Your review is requested";
  if (pr.ci === "FAILURE" || pr.ci === "ERROR") return "CI failing";
  if (pr.review === "CHANGES_REQUESTED") return "Changes requested";
  if (pr.review === "APPROVED" && !pr.isDraft && (pr.ci === undefined || pr.ci === "SUCCESS")) return "Approved, ready to merge";
}

function classify(session: Session | undefined, prs: Pr[], now: number): Pick<Row, "bucket" | "reason" | "stale" | "age"> {
  const age = now - Math.max(session?.lastActivity ?? 0, ...prs.map((p) => p.updatedAt));
  const stale = age > STALE_DAYS * DAY;
  if (session?.needsUser) return { bucket: "needs", reason: session.needsUser, stale: false, age };
  if (session?.running) return { bucket: "running", reason: "Working now", stale: false, age };
  const need = prs.map(prNeeds).find(Boolean);
  if (need) return { bucket: "needs", reason: need, stale: false, age };
  if (prs.length && prs.every((p) => p.state !== "OPEN")) {
    const merged = prs.some((p) => p.state === "MERGED");
    const reason = (merged ? "Merged" : "Closed") + (session ? ", archive me" : "");
    return { bucket: "done", reason, stale: false, age };
  }
  const open = prs.find((p) => p.state === "OPEN");
  const reason = open ? (open.isDraft ? "Draft PR" : open.ci === "PENDING" ? "CI running" : "PR open, waiting") : "Idle session";
  return { bucket: "idle", reason, stale, age };
}

export function buildRows(sessions: Session[], livePrs: Pr[], now = Date.now()): Row[] {
  const live = new Map(livePrs.map((p) => [`${p.repo}#${p.number}`, p]));
  const claimed = new Set<string>();
  const rows: Row[] = [];
  for (const s of sessions) {
    const prs = s.prs.map((sp): Pr => {
      const key = `${sp.repo}#${sp.number}`;
      claimed.add(key);
      // Fall back to the session file's last-known state for PRs outside the live search window.
      return live.get(key) ?? { repo: sp.repo, number: sp.number, title: "", url: sp.url, state: sp.state, updatedAt: 0, isDraft: false, reviewRequested: false };
    });
    rows.push({ ...classify(s, prs, now), session: s, prs, title: s.title, project: prs[0]?.repo ?? s.project });
  }
  for (const [key, pr] of live) {
    if (!claimed.has(key)) rows.push({ ...classify(undefined, [pr], now), prs: [pr], title: pr.title, project: pr.repo });
  }
  return rows.sort((a, b) => a.age - b.age);
}

const esc = (s: string) => s.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);

function ago(ms: number) {
  const m = Math.round(ms / 60_000);
  if (m < 60) return `${m}m`;
  if (m < 60 * 48) return `${Math.round(m / 60)}h`;
  return `${Math.round(m / 1440)}d`;
}

const SECTIONS: [Bucket, string][] = [
  ["needs", "Needs me"],
  ["running", "Running"],
  ["idle", "Open, idle"],
  ["done", `Recently done`],
];

export function render(rows: Row[], warnings: string[], now = Date.now()) {
  const row = (r: Row) => {
    const links = [
      r.session ? `<a href="claude://claude.ai/epitaxy/${esc(r.session.id)}">Session</a>` : "",
      ...r.prs.map((p) => `<a href="${esc(p.url)}" target="_blank">#${p.number}</a>`),
    ].join(" ");
    const recap = r.session?.recap && r.bucket !== "needs" ? `<div class="recap">${esc(r.session.recap)}</div>` : "";
    return `<li class="${r.stale ? "stale" : ""}">
      <div class="top"><span class="title">${esc(r.title)}</span><span class="links">${links}</span></div>
      <div class="meta"><span class="project">${esc(r.project)}</span> · ${ago(r.age)} ago · <span class="reason">${esc(r.reason)}</span>${r.stale ? ` · <b>stale</b>` : ""}</div>
      ${recap}</li>`;
  };
  const sections = SECTIONS.map(([b, label]) => {
    const items = rows.filter((r) => r.bucket === b);
    return `<section class="${b}"><h2>${label} <span class="count">${items.length}</span></h2><ul>${items.map(row).join("") || `<li class="empty">Nothing here</li>`}</ul></section>`;
  }).join("");
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="60"><title>In flight</title><style>
:root{--bg:#fafaf9;--fg:#1c1917;--muted:#78716c;--line:#e7e5e4;--card:#fff;--needs:#dc2626;--running:#2563eb;--idle:#78716c;--done:#16a34a}
@media (prefers-color-scheme:dark){:root{--bg:#0c0a09;--fg:#e7e5e4;--muted:#a8a29e;--line:#292524;--card:#1c1917}}
body{margin:0;padding:24px 16px;background:var(--bg);color:var(--fg);font:14px/1.45 -apple-system,system-ui,sans-serif}
main{max-width:960px;margin:0 auto}header{display:flex;justify-content:space-between;align-items:baseline;color:var(--muted)}
h1{margin:0;font-size:20px;color:var(--fg)}h2{font-size:13px;text-transform:uppercase;letter-spacing:.06em;margin:28px 0 8px}
.count{color:var(--muted);font-weight:400}ul{list-style:none;margin:0;padding:0}
li{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--c);border-radius:6px;padding:10px 12px;margin-bottom:6px}
section{--c:var(--idle)}.needs{--c:var(--needs)}.running{--c:var(--running)}.done{--c:var(--done)}h2{color:var(--c)}
.top{display:flex;justify-content:space-between;gap:12px}.title{font-weight:600}.links{white-space:nowrap}.links a{margin-left:8px}
a{color:var(--running)}.meta,.recap{color:var(--muted);font-size:13px}.reason{color:var(--fg)}.recap{margin-top:4px}
li.stale{opacity:.6}li.empty{border-left-color:var(--line);color:var(--muted)}
.warn{background:#fef3c7;color:#78350f;padding:8px 12px;border-radius:6px;margin-top:12px}
</style></head><body><main><header><h1>In flight</h1><span>Updated ${new Date(now).toLocaleTimeString()}</span></header>
${warnings.map((w) => `<div class="warn">${esc(w)}</div>`).join("")}${sections}</main></body></html>`;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  createServer(async (req, res) => {
    if (req.url !== "/") return res.writeHead(404).end();
    try {
      const now = Date.now();
      const s = loadSessions();
      const p = await loadPrs(now);
      res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
      res.end(render(buildRows(s.sessions, p.prs, now), [...s.warnings, ...p.warnings], now));
    } catch (e) {
      // One bad record must not take the long-running server down.
      console.error(e);
      res.writeHead(500, { "content-type": "text/plain" }).end(`Dashboard error: ${(e as Error).message}`);
    }
  }).listen(PORT, "127.0.0.1", () => console.log(`In flight: http://localhost:${PORT}`));
}
