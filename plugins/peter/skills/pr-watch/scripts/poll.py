#!/usr/bin/env python3
"""Poll GitHub read-only; leave changed heads pending for the review workflow.

State is schemaVersion 1: {scope: ["owner/repo"], prs: {"owner/repo#1": {...}}}.
A PR baseline uses repo, number, headSha, baseSha, baseRef, state, isDraft,
reviewedHeadSha, checks, lastSeenCommentIds, and lastSeenReviewIds. Existing
extra fields are preserved. Missing content signatures are learned on a quiet
poll. Never infer reviewedHeadSha from headSha. Review/reconciliation is the
caller's job; this helper writes the baseline only when no changes are pending.
"""

import argparse
import concurrent.futures
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


PAGE = "pageInfo{hasNextPage endCursor}"
PR_FIELDS = "number title url headRefOid baseRefOid baseRefName state isDraft mergeStateStatus"
COMMENT_FIELDS = "id url body createdAt updatedAt author{login}"
REVIEW_FIELDS = "id url body submittedAt state author{login} commit{oid}"
THREAD_COMMENT_FIELDS = "id url body createdAt updatedAt author{login}"
THREAD_FIELDS = (
    "id isResolved isOutdated path line comments(first:100){"
    + PAGE + " nodes{" + THREAD_COMMENT_FIELDS + "}}"
)
CHECK_FIELDS = (
    "__typename ... on CheckRun{id name status conclusion detailsUrl startedAt completedAt} "
    "... on StatusContext{id context state targetUrl createdAt}"
)


def gh(args):
    result = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "GitHub CLI request failed")
    payload = json.loads(result.stdout)
    if isinstance(payload, dict) and payload.get("errors"):
        raise RuntimeError("GitHub GraphQL: " + "; ".join(
            str(error.get("message", error)) for error in payload["errors"]
        ))
    return payload


def graphql(query, **variables):
    args = ["api", "graphql", "-f", "query=" + query]
    for key, value in variables.items():
        if value is not None:
            args.extend(["-F" if isinstance(value, int) else "-f", f"{key}={value}"])
    return gh(args)["data"]


def paginated(fetch):
    """Drain a GraphQL connection; missing/nonadvancing cursors fail closed."""
    cursor, seen, rows = None, set(), []
    while True:
        connection = fetch(cursor)
        if connection is None:  # A commit with no status rollup has no checks.
            if cursor is not None:
                raise RuntimeError("Incomplete GitHub pagination: connection disappeared")
            return rows
        rows.extend(connection["nodes"])
        page = connection["pageInfo"]
        if not page["hasNextPage"]:
            return rows
        cursor = page.get("endCursor")
        if not cursor or cursor in seen:
            raise RuntimeError("Incomplete GitHub pagination: missing or repeated cursor")
        seen.add(cursor)


def repo_variables(repo):
    owner, name = repo.split("/")
    return {"owner": owner, "name": name}


def inventory(repo):
    query = (
        "query Inventory($owner:String!,$name:String!,$cursor:String){"
        "repository(owner:$owner,name:$name){pullRequests(states:OPEN,first:100,"
        "after:$cursor,orderBy:{field:CREATED_AT,direction:ASC}){"
        + PAGE + " nodes{" + PR_FIELDS + "}}}}"
    )
    return {"repo": repo, "prs": paginated(lambda cursor: graphql(
        query, **repo_variables(repo), cursor=cursor
    )["repository"]["pullRequests"])}


def metadata(repo, number):
    query = (
        "query PullRequest($owner:String!,$name:String!,$num:Int!){"
        "repository(owner:$owner,name:$name){pullRequest(number:$num){"
        + PR_FIELDS + "}}}"
    )
    result = graphql(query, **repo_variables(repo), num=number)["repository"]["pullRequest"]
    if not result:
        raise RuntimeError(f"Pull request unavailable: {repo}#{number}")
    return result


def pr_connection(repo, number, field, fields):
    query = (
        "query " + field.capitalize() + "($owner:String!,$name:String!,$num:Int!,$cursor:String){"
        "repository(owner:$owner,name:$name){pullRequest(number:$num){"
        + field + "(first:100,after:$cursor){" + PAGE + " nodes{" + fields + "}}}}}"
    )
    return paginated(lambda cursor: graphql(
        query, **repo_variables(repo), num=number, cursor=cursor
    )["repository"]["pullRequest"][field])


def review_threads(repo, number):
    rows = pr_connection(repo, number, "reviewThreads", THREAD_FIELDS)
    query = (
        "query ThreadComments($id:ID!,$cursor:String){node(id:$id){"
        "... on PullRequestReviewThread{comments(first:100,after:$cursor){"
        + PAGE + " nodes{" + THREAD_COMMENT_FIELDS + "}}}}}"
    )
    for row in rows:
        initial = row["comments"]
        if initial["pageInfo"]["hasNextPage"]:
            # Fetch from the start to use one pagination implementation for all sizes.
            comments = paginated(lambda cursor: graphql(
                query, id=row["id"], cursor=cursor
            )["node"]["comments"])
            row["comments"] = {"nodes": comments}
        else:
            row["comments"] = {"nodes": initial["nodes"]}
    return rows


def status_checks(repo, sha):
    query = (
        "query Checks($owner:String!,$name:String!,$sha:GitObjectID!,$cursor:String){"
        "repository(owner:$owner,name:$name){object(oid:$sha){... on Commit{"
        "statusCheckRollup{contexts(first:100,after:$cursor){"
        + PAGE + " nodes{" + CHECK_FIELDS + "}}}}}}}"
    )

    def fetch(cursor):
        commit = graphql(query, **repo_variables(repo), sha=sha, cursor=cursor)["repository"]["object"]
        if commit is None:
            raise RuntimeError(f"Head commit unavailable: {repo}@{sha}")
        rollup = commit["statusCheckRollup"]
        return rollup["contexts"] if rollup is not None else None

    return paginated(fetch)


def details(pair):
    repo, number = pair
    data = metadata(repo, number)
    data["repo"] = repo
    data["comments"] = pr_connection(repo, number, "comments", COMMENT_FIELDS)
    data["reviews"] = pr_connection(repo, number, "reviews", REVIEW_FIELDS)
    data["reviewThreads"] = review_threads(repo, number)
    data["statusCheckRollup"] = status_checks(repo, data["headRefOid"])
    after = metadata(repo, number)
    if any(data[key] != after[key] for key in (
        "headRefOid", "baseRefOid", "baseRefName", "state", "isDraft"
    )):
        raise RuntimeError(f"Pull request changed while polling; retry: {repo}#{number}")
    data["mergeStateStatus"] = after["mergeStateStatus"]
    return data


def parallel(function, items):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        return list(pool.map(function, items))


def checks(rows):
    return [{
        "name": row.get("name") or row.get("context"),
        "status": row.get("status") or row.get("state") or None,
        "conclusion": row.get("conclusion") or None,
        "url": row.get("detailsUrl") or row.get("targetUrl") or row.get("url"),
    } for row in rows]


def check_signature(rows):
    return sorted(((r["name"], r["status"], r["conclusion"]) for r in checks(rows)), key=repr)


def content_signatures(rows):
    return {row["id"]: hashlib.sha256(json.dumps(
        row, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest() for row in rows}


def thread_signature(rows):
    """Compare the fields present in the original v1 baseline, ignoring page metadata."""
    return sorted((
        row["id"], row.get("isResolved"), row.get("isOutdated"), row.get("path"), row.get("line"),
        sorted((c["id"], c.get("updatedAt")) for c in row["comments"]["nodes"]),
    ) for row in rows)


def compare(state, current, thread_states):
    changes = []
    for item in current:
        key = f'{item["repo"]}#{item["number"]}'
        old, changed = state["prs"].get(key), []
        if old is None:
            changed.append("new")
        else:
            for before, after in (("headSha", "headRefOid"), ("baseSha", "baseRefOid"),
                                  ("baseRef", "baseRefName"), ("state", "state"), ("isDraft", "isDraft")):
                if old.get(before) != item.get(after):
                    changed.append(after)
            if check_signature(old.get("checks", [])) != check_signature(item["statusCheckRollup"]):
                changed.append("checks")
            merge = item["mergeStateStatus"]
            if merge != "UNKNOWN" and merge != old.get("lastDefinitiveMergeStateStatus", old.get("mergeStateStatus")):
                changed.append("mergeStateStatus")
            for field, seen, signatures in (("comments", "lastSeenCommentIds", "commentSignatures"),
                                             ("reviews", "lastSeenReviewIds", "reviewSignatures")):
                if (set(old.get(seen, [])) != {r["id"] for r in item[field]} or
                    (signatures in old and old[signatures] != content_signatures(item[field]))):
                    changed.append(field)
            if old.get("reviewThreads") is not None and thread_signature(old["reviewThreads"]) != thread_signature(thread_states[key]):
                changed.append("reviewThreads")
        if old is None or old.get("reviewedHeadSha") != item["headRefOid"]:
            changed.append("unreviewedHead")
        if old is not None and "reviewedBaseSha" in old and old["reviewedBaseSha"] != item["baseRefOid"]:
            changed.append("unreviewedBase")
        if old is not None and old.get("pendingPublication"):
            changed.append("pendingPublication")
        if changed:
            changes.append({"pr": key, "changes": changed, "url": item["url"],
                            "head": item["headRefOid"], "state": item["state"]})
    return changes


def atomic_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as output:
            json.dump(value, output, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        if path.exists():
            os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def poll(state_path, snapshot_path):
    original = state_path.read_bytes()
    state = json.loads(original)
    if state.get("schemaVersion", 1) != 1:
        raise ValueError("Unsupported schemaVersion; expected 1")
    scope = state.get("scope")
    if not isinstance(scope, list) or not all(isinstance(r, str) and re.fullmatch(r"[\w.-]+/[\w.-]+", r) for r in scope):
        raise ValueError("State scope must be a list of owner/repo strings")
    if not isinstance(state.get("prs"), dict):
        raise ValueError("State prs must be an object keyed by owner/repo#number")
    inventories = parallel(inventory, sorted(set(scope)))
    pairs = {(row["repo"], p["number"]) for row in inventories for p in row["prs"]}
    pairs.update((old["repo"], old["number"]) for old in state["prs"].values()
                 if old["repo"] in scope and (
                     old["state"] == "OPEN" or old.get("pendingPublication") or
                     old.get("reviewedHeadSha") != old.get("headSha") or
                     ("reviewedBaseSha" in old and old["reviewedBaseSha"] != old.get("baseSha"))
                 ))
    current = parallel(details, sorted(pairs))
    thread_states = {f'{p["repo"]}#{p["number"]}': p.pop("reviewThreads") for p in current}
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    changes = compare(state, current, thread_states)
    open_count = sum(p["state"] == "OPEN" for p in current)
    snapshot = {"checkedAt": now, "inventory": inventories, "details": current,
                "reviewThreads": thread_states, "changes": changes}
    if state_path.read_bytes() != original:
        raise RuntimeError("Baseline changed during polling; retry without overwriting it")
    atomic_write(snapshot_path, snapshot)
    if not changes:
        updated = copy.deepcopy(state)
        updated["schemaVersion"] = 1
        for item in current:
            key = f'{item["repo"]}#{item["number"]}'
            old = updated["prs"][key]
            old["checks"] = checks(item["statusCheckRollup"])
            old["mergeStateStatus"] = item["mergeStateStatus"]
            if item["mergeStateStatus"] != "UNKNOWN":
                old["lastDefinitiveMergeStateStatus"] = item["mergeStateStatus"]
            old["reviewThreads"] = thread_states[key]
            old["commentSignatures"] = content_signatures(item["comments"])
            old["reviewSignatures"] = content_signatures(item["reviews"])
        updated["updatedAt"] = now
        updated["checkerScript"] = str(Path(__file__).resolve())
        updated["lastHeartbeatSummary"] = {"openCount": open_count, "newFindings": 0,
                                           "meaningfulChanges": 0, "notification": "silent"}
        if state_path.read_bytes() != original:
            raise RuntimeError("Baseline changed during snapshot write; retry without overwriting it")
        atomic_write(state_path, updated)
    return {"openCount": open_count, "changes": changes,
            "baselineUpdated": not changes, "snapshot": str(snapshot_path)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True, type=Path, help="Existing schemaVersion 1 baseline JSON")
    parser.add_argument("--snapshot", type=Path, help="Defaults to pr-watch-current.json beside the baseline")
    args = parser.parse_args(argv)
    state_path = args.state.expanduser().resolve()
    snapshot_path = (args.snapshot.expanduser().resolve() if args.snapshot else
                     state_path.with_name("pr-watch-current.json"))
    if state_path == snapshot_path:
        parser.error("--snapshot must differ from --state")
    try:
        print(json.dumps(poll(state_path, snapshot_path)))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({"error": str(error), "baselineUpdated": False}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
