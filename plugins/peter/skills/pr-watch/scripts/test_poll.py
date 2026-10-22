"""Offline contract fixtures: no GitHub credentials, network, or external packages."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import poll


REPO = "example/project"
KEY = REPO + "#1"


def connection(rows, more=False, cursor=None):
    return {"nodes": rows, "pageInfo": {"hasNextPage": more, "endCursor": cursor}}


def item():
    return {
        "repo": REPO, "number": 1, "title": "Example change", "url": "https://github.com/" + KEY,
        "headRefOid": "head-a", "baseRefOid": "base-a", "baseRefName": "main", "state": "OPEN",
        "isDraft": False, "mergeStateStatus": "CLEAN", "comments": [], "reviews": [],
        "reviewThreads": [], "statusCheckRollup": [
            {"name": "test", "status": "COMPLETED", "conclusion": "SUCCESS"}
        ],
    }


def state():
    return {
        "schemaVersion": 1, "scope": [REPO], "knownOpenFindings": {KEY: ["Existing finding"]},
        "prs": {KEY: {
            "repo": REPO, "number": 1, "headSha": "head-a", "baseSha": "base-a", "baseRef": "main",
            "reviewedHeadSha": "head-a", "reviewedBaseSha": "base-a", "state": "OPEN", "isDraft": False,
            "lastDefinitiveMergeStateStatus": "CLEAN", "lastSeenCommentIds": [], "lastSeenReviewIds": [],
            "checks": poll.checks(item()["statusCheckRollup"]), "latestReviewUrl": "https://example.test/review",
        }},
    }


class PollStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "state.json"
        self.snapshot = self.path.with_name("snapshot.json")
        self.write(state())

    def write(self, value):
        self.path.write_text(json.dumps(value))

    def run_poll(self, current=None, inventory_rows=None):
        current = item() if current is None else current
        inventory_rows = [current] if inventory_rows is None else inventory_rows
        with mock.patch.object(poll, "inventory", return_value={"repo": REPO, "prs": inventory_rows}), \
             mock.patch.object(poll, "details", side_effect=lambda pair: copy.deepcopy(current)):
            return poll.poll(self.path, self.snapshot)

    def test_quiet_poll_preserves_review_evidence_and_migrates_optional_fields(self):
        original = state()
        del original["schemaVersion"]
        del original["prs"][KEY]["reviewedBaseSha"]  # Evidence migration belongs to the coordinator.
        self.write(original)
        result = self.run_poll()
        updated = json.loads(self.path.read_text())
        self.assertTrue(result["baselineUpdated"])
        self.assertEqual(updated["prs"][KEY]["reviewedHeadSha"], "head-a")
        self.assertNotIn("reviewedBaseSha", updated["prs"][KEY])
        self.assertEqual(updated["knownOpenFindings"], original["knownOpenFindings"])
        self.assertEqual(updated["prs"][KEY]["latestReviewUrl"], "https://example.test/review")
        self.assertEqual(updated["prs"][KEY]["commentSignatures"], {})

    def test_new_head_stays_pending_across_repeated_polls(self):
        before = self.path.read_bytes()
        current = item()
        current["headRefOid"] = "head-b"
        for _ in range(2):
            result = self.run_poll(current)
            self.assertIn("unreviewedHead", result["changes"][0]["changes"])
            self.assertFalse(result["baselineUpdated"])
            self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(json.loads(self.snapshot.read_text())["details"][0]["headRefOid"], "head-b")

    def test_checks_change_is_seen_even_when_head_is_unchanged(self):
        current = item()
        current["statusCheckRollup"][0]["conclusion"] = "FAILURE"
        self.assertEqual(self.run_poll(current)["changes"][0]["changes"], ["checks"])

    def test_queued_check_empty_conclusion_migrates_to_null_without_alert(self):
        old = state()
        old["prs"][KEY]["checks"] = [{"name": "test", "status": "QUEUED", "conclusion": ""}]
        self.write(old)
        current = item()
        current["statusCheckRollup"] = [{"name": "test", "status": "QUEUED", "conclusion": None}]
        self.assertTrue(self.run_poll(current)["baselineUpdated"])
        self.assertIsNone(json.loads(self.path.read_text())["prs"][KEY]["checks"][0]["conclusion"])

    def test_new_pr_is_not_marked_reviewed(self):
        self.write({"scope": [REPO], "prs": {}})
        before = self.path.read_bytes()
        self.assertEqual(self.run_poll()["changes"][0]["changes"], ["new", "unreviewedHead"])
        self.assertEqual(self.path.read_bytes(), before)

    def test_reviewed_base_mismatch_remains_pending_after_observed_base_advances(self):
        old = state()
        old["prs"][KEY]["baseSha"] = "base-b"
        self.write(old)
        current = item()
        current["baseRefOid"] = "base-b"
        result = self.run_poll(current)
        self.assertEqual(result["changes"][0]["changes"], ["unreviewedBase"])
        self.assertFalse(result["baselineUpdated"])

    def test_pending_publication_on_merged_pr_is_still_polled(self):
        old = state()
        old["prs"][KEY]["state"] = "MERGED"
        old["prs"][KEY]["pendingPublication"] = {"head": "head-a", "fingerprint": "pending"}
        self.write(old)
        current = item()
        current["state"] = "MERGED"
        result = self.run_poll(current, inventory_rows=[])
        self.assertEqual(result["changes"][0]["changes"], ["pendingPublication"])
        self.assertFalse(result["baselineUpdated"])

    def test_merged_pending_head_is_not_dropped_from_poll(self):
        old = state()
        old["prs"][KEY].update(state="MERGED", reviewedHeadSha="older-head")
        self.write(old)
        current = item()
        current["state"] = "MERGED"
        self.assertIn("unreviewedHead", self.run_poll(current, inventory_rows=[])["changes"][0]["changes"])

    def test_previously_open_pr_is_checked_after_it_leaves_inventory(self):
        current = item()
        current["state"] = "CLOSED"
        result = self.run_poll(current, inventory_rows=[])
        self.assertEqual(result["openCount"], 0)
        self.assertIn("state", result["changes"][0]["changes"])

    def test_unknown_merge_state_does_not_erase_last_definitive_state(self):
        current = item()
        current["mergeStateStatus"] = "UNKNOWN"
        self.assertTrue(self.run_poll(current)["baselineUpdated"])
        self.assertEqual(json.loads(self.path.read_text())["prs"][KEY]["lastDefinitiveMergeStateStatus"], "CLEAN")

    def test_content_edits_are_detected_after_signature_migration(self):
        current = item()
        comment = {"id": "comment-1", "body": "before", "updatedAt": "same-time"}
        current["comments"] = [comment]
        old = state()
        old["prs"][KEY].update(lastSeenCommentIds=["comment-1"], commentSignatures=poll.content_signatures([comment]))
        self.write(old)
        current["comments"][0]["body"] = "after"
        self.assertIn("comments", self.run_poll(current)["changes"][0]["changes"])

    def test_thread_migration_ignores_added_body_fields_but_detects_edits(self):
        old = state()
        thread = {"id": "thread-1", "isResolved": False, "isOutdated": False, "path": "file.py", "line": 1,
                  "comments": {"nodes": [{"id": "comment-1", "updatedAt": "before"}]}}
        old["prs"][KEY]["reviewThreads"] = [thread]
        self.write(old)
        current = item()
        current["reviewThreads"] = copy.deepcopy([thread])
        current["reviewThreads"][0]["comments"]["nodes"][0]["body"] = "body"
        self.assertTrue(self.run_poll(current)["baselineUpdated"])
        current["reviewThreads"][0]["comments"]["nodes"][0]["updatedAt"] = "after"
        self.assertIn("reviewThreads", self.run_poll(current)["changes"][0]["changes"])

    def test_fetch_error_preserves_complete_baseline_and_snapshot(self):
        before = self.path.read_bytes()
        self.snapshot.write_text("previous complete snapshot")
        with mock.patch.object(poll, "inventory", side_effect=RuntimeError("pagination failed")):
            with self.assertRaisesRegex(RuntimeError, "pagination failed"):
                poll.poll(self.path, self.snapshot)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.snapshot.read_text(), "previous complete snapshot")

    def test_concurrent_baseline_edit_is_not_overwritten(self):
        replacement = state()
        replacement["ownerNote"] = "updated during poll"
        def changed(_):
            self.write(replacement)
            return item()
        with mock.patch.object(poll, "inventory", return_value={"repo": REPO, "prs": [item()]}), \
             mock.patch.object(poll, "details", side_effect=changed):
            with self.assertRaisesRegex(RuntimeError, "Baseline changed"):
                poll.poll(self.path, self.snapshot)
        self.assertEqual(json.loads(self.path.read_text()), replacement)
        self.assertFalse(self.snapshot.exists())

    def test_atomic_replace_failure_keeps_previous_file_and_cleans_temp(self):
        before = self.path.read_bytes()
        with mock.patch.object(poll.os, "replace", side_effect=OSError("write failed")):
            with self.assertRaises(OSError):
                poll.atomic_write(self.path, {"replacement": True})
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])


class PaginationTests(unittest.TestCase):
    def test_every_connection_drains_all_pages(self):
        for field, fetch in (
            ("pullRequests", lambda: poll.inventory(REPO)["prs"]),
            ("comments", lambda: poll.pr_connection(REPO, 1, "comments", poll.COMMENT_FIELDS)),
            ("reviews", lambda: poll.pr_connection(REPO, 1, "reviews", poll.REVIEW_FIELDS)),
            ("contexts", lambda: poll.status_checks(REPO, "head-a")),
        ):
            with self.subTest(field=field):
                calls = []
                def reply(query, **variables):
                    self.assertEqual(query.count("{"), query.count("}"))
                    calls.append(variables.get("cursor"))
                    page = connection(list(range(100)), True, "page-2") if variables.get("cursor") is None else connection([100])
                    if field == "pullRequests": return {"repository": {field: page}}
                    if field == "contexts": return {"repository": {"object": {"statusCheckRollup": {field: page}}}}
                    return {"repository": {"pullRequest": {field: page}}}
                with mock.patch.object(poll, "graphql", side_effect=reply):
                    self.assertEqual(fetch(), list(range(101)))
                self.assertEqual(calls, [None, "page-2"])

    def test_nested_thread_comments_and_outer_threads_both_paginate(self):
        first = {"id": "thread-1", "comments": connection([{"id": str(i)} for i in range(100)], True, "comments-2")}
        second = {"id": "thread-2", "comments": connection([])}
        def reply(query, **variables):
            self.assertEqual(query.count("{"), query.count("}"))
            if "query ThreadComments" in query:
                page = first["comments"] if variables.get("cursor") is None else connection([{"id": "100"}])
                return {"node": {"comments": page}}
            page = connection([copy.deepcopy(first)], True, "threads-2") if variables.get("cursor") is None else connection([second])
            return {"repository": {"pullRequest": {"reviewThreads": page}}}
        with mock.patch.object(poll, "graphql", side_effect=reply):
            rows = poll.review_threads(REPO, 1)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(rows[0]["comments"]["nodes"]), 101)
        self.assertEqual(rows[0]["comments"]["nodes"][-1]["id"], "100")

    def test_missing_and_repeated_cursors_fail_instead_of_truncating(self):
        for cursor in (None, "same"):
            with self.subTest(cursor=cursor), self.assertRaisesRegex(RuntimeError, "pagination"):
                poll.paginated(lambda _: connection([1], True, cursor))

    def test_connection_disappearing_mid_page_fails_instead_of_truncating(self):
        with self.assertRaisesRegex(RuntimeError, "pagination"):
            poll.paginated(lambda cursor: connection([1], True, "next") if cursor is None else None)

    def test_no_status_rollup_means_no_checks(self):
        with mock.patch.object(poll, "graphql", return_value={"repository": {"object": {"statusCheckRollup": None}}}):
            self.assertEqual(poll.status_checks(REPO, "head-a"), [])

    def test_metadata_change_mid_poll_fails_closed(self):
        after = item()
        after["headRefOid"] = "head-b"
        with mock.patch.object(poll, "metadata", side_effect=[item(), after]), \
             mock.patch.object(poll, "pr_connection", return_value=[]), \
             mock.patch.object(poll, "review_threads", return_value=[]), \
             mock.patch.object(poll, "status_checks", return_value=[]):
            with self.assertRaisesRegex(RuntimeError, "changed while polling"):
                poll.details((REPO, 1))


if __name__ == "__main__":
    unittest.main()
