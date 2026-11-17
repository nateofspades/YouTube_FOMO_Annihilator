"""Exercise collection against a real HTTP server, without YouTube credentials."""

import json
import threading
import unittest
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from scripts import update_leaderboard as update


class CollectionReliabilityTests(unittest.TestCase):
    respond = staticmethod(lambda request: (200, {}, {}))
    requests = []

    @classmethod
    def setUpClass(cls):
        cls.requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                url = urlsplit(self.path)
                params = parse_qs(url.query)
                cls.requests.append((url.path.rsplit("/", 1)[-1], params))
                status, payload, headers = cls.respond(cls.requests[-1])
                body = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                for name, value in headers.items():
                    self.send_header(name, value)
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass  # Never print request URLs (they contain the API key).

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        type(self).requests = []
        type(self).respond = staticmethod(self.source_response)
        self.base = patch.object(update, "API_BASE", f"http://127.0.0.1:{self.server.server_port}")
        self.base.start()
        self.addCleanup(self.base.stop)

    @staticmethod
    def error(code, reason):
        return {"error": {"code": code, "message": reason, "errors": [{"reason": reason}]}}

    @staticmethod
    def source_response(request):
        resource, params = request
        if resource == "channels":
            handle = params["forHandle"][0]
            return 200, {"items": [{"id": handle, "contentDetails": {"relatedPlaylists": {"uploads": handle}}}]}, {}
        if resource == "playlistItems":
            if params["playlistId"] == ["@missing"]:
                return 404, CollectionReliabilityTests.error(404, "playlistNotFound"), {}
            return 200, {"items": [{"contentDetails": {"videoId": "good-video", "videoPublishedAt": "2026-11-17T10:00:00Z"}}]}, {}
        if resource == "videos":
            return 200, {"items": [{"id": "good-video", "snippet": {"title": "AI news", "publishedAt": "2026-11-17T10:00:00Z", "defaultAudioLanguage": "en", "channelId": "@good"}, "statistics": {"viewCount": "100"}}]}, {}
        raise AssertionError(resource)

    def collect(self, channels=None):
        return update.collect_leaderboard(
            "test-key", datetime(2026, 11, 17, 18, tzinfo=timezone.utc),
            slug="test", title="Test", terms=("ai",), universe_version=1,
            channels=channels if channels is not None else [
                {"name": "Missing playlist", "handle": "@missing", "source_type": "Creator"},
                {"name": "Working channel", "handle": "@good", "source_type": "Creator"},
            ],
        )

    def test_temporary_server_errors_are_retried_before_succeeding(self):
        def respond(request):
            if len(self.requests) < 3:
                return 503, self.error(503, "backendError"), {}
            return 200, {"items": []}, {}

        type(self).respond = staticmethod(respond)
        with patch("time.sleep") as sleep:
            payload = update.youtube_get("videos", {"id": "example"}, "test-key")
        self.assertEqual(payload, {"items": []})
        self.assertEqual(len(self.requests), 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2])

    def test_permanent_api_failures_are_not_skipped_or_retried(self):
        for status, reason in [(403, "quotaExceeded"), (400, "keyInvalid"), (401, "unauthorized"), (403, "forbidden"), (404, "unknownNotFound")]:
            with self.subTest(reason=reason):
                self.requests.clear()
                type(self).respond = staticmethod(lambda request: (status, self.error(status, reason), {}))
                with patch("time.sleep") as sleep:
                    with self.assertRaisesRegex(RuntimeError, reason) as caught:
                        self.collect()
                self.assertNotIsInstance(caught.exception, update.SourceUnavailable)
                self.assertEqual(len(self.requests), 1)
                sleep.assert_not_called()

    def test_private_uploads_playlist_is_isolated(self):
        def respond(request):
            resource, params = request
            if resource == "playlistItems" and params["playlistId"] == ["@missing"]:
                return 403, self.error(403, "playlistItemsNotAccessible"), {}
            return self.source_response(request)

        type(self).respond = staticmethod(respond)
        payload = self.collect()
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["source_channels"][0]["status"], "unavailable")

    def test_failure_after_first_playlist_page_does_not_publish_partial_source(self):
        def respond(request):
            resource, params = request
            if resource == "playlistItems" and params["playlistId"] == ["@missing"]:
                if "pageToken" in params:
                    return 404, self.error(404, "playlistNotFound"), {}
                return 200, {"items": [{"contentDetails": {"videoId": "partial", "videoPublishedAt": "2026-11-17T10:00:00Z"}}], "nextPageToken": "second"}, {}
            return self.source_response(request)

        type(self).respond = staticmethod(respond)
        payload = self.collect()
        self.assertEqual(payload["candidate_count"], 1)
        self.assertEqual(payload["source_channels"][0]["recent_video_count"], 0)
        self.assertFalse(any("partial" in params.get("id", []) for resource, params in self.requests))

    def test_empty_working_playlist_is_not_an_unavailable_source(self):
        def respond(request):
            if request[0] == "playlistItems":
                return 200, {"items": []}, {}
            return self.source_response(request)

        type(self).respond = staticmethod(respond)
        payload = self.collect()
        self.assertEqual(payload["results"], [])
        self.assertTrue(all("status" not in source for source in payload["source_channels"]))

    def test_rate_limits_are_retried(self):
        for status, reason in [(429, "rateLimitExceeded"), (403, "rateLimitExceeded"), (403, "userRateLimitExceeded")]:
            with self.subTest(status=status, reason=reason):
                self.requests.clear()
                type(self).respond = staticmethod(lambda request: (status, self.error(status, reason), {}) if len(self.requests) == 1 else (200, {"items": []}, {}))
                with patch("time.sleep") as sleep:
                    self.assertEqual(update.youtube_get("videos", {}, "test-key"), {"items": []})
                self.assertEqual(len(self.requests), 2)
                sleep.assert_called_once_with(1)

    def test_persistent_transient_error_stops_after_four_attempts(self):
        type(self).respond = staticmethod(lambda request: (503, self.error(503, "backendError"), {}))
        with patch("time.sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "exhausted 4 attempts"):
                update.youtube_get("videos", {}, "test-key")
        self.assertEqual(len(self.requests), 4)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2, 4])

    def test_network_errors_and_timeouts_are_retried_without_leaking_keys(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from urllib.error import URLError

        for error in [URLError("https://example.invalid/?key=test-key"), TimeoutError("key=test-key"), ConnectionResetError("key=test-key")]:
            with self.subTest(error=type(error).__name__):
                output = StringIO()
                with patch.object(update, "urlopen", side_effect=error) as get, patch("time.sleep"), redirect_stdout(output):
                    with self.assertRaisesRegex(RuntimeError, "exhausted 4 attempts") as caught:
                        update.youtube_get("videos", {}, "test-key")
                self.assertEqual(get.call_count, 4)
                self.assertNotIn("test-key", output.getvalue() + str(caught.exception))
                self.assertTrue(caught.exception.__suppress_context__)

    def test_all_sources_unavailable_fails_instead_of_publishing_an_empty_category(self):
        with self.assertRaisesRegex(RuntimeError, "No available sources.*test"):
            self.collect(channels=[{"name": "Missing", "handle": "@missing", "source_type": "Creator"}])

    def test_missing_uploads_playlist_does_not_abort_other_sources(self):
        payload = self.collect()
        self.assertEqual([row["video_id"] for row in payload["results"]], ["good-video"])
        missing, working = payload["source_channels"]
        self.assertEqual(missing["status"], "unavailable")
        self.assertEqual(missing["channel_id"], "@missing")
        self.assertEqual(missing["recent_video_count"], 0)
        self.assertIn("playlistNotFound", missing["error"])
        self.assertEqual(working["recent_video_count"], 1)


if __name__ == "__main__":
    unittest.main()
