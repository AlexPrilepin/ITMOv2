"""Регрессии безопасности по THREAT_MODEL.md (T1–T13).

Каждый тест описывает безопасное поведение; на исходном service.py он падает
(вывод — evidence/before/test_security.txt), после исправлений проходит.
"""

import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from service import Shop, make_handler


class SecurityTest(unittest.TestCase):
    def setUp(self):
        self.shop = Shop()
        self.addCleanup(self.shop.close)

    def request(self, method, path, body=None, headers=None):
        with self.shop.lock:
            return self.shop.dispatch(method, path, body or {}, headers or {})

    def login(self, username="alice", password=None):
        status, result = self.request("POST", "/login", {"username": username, "password": password or f"learn-{username}"})
        self.assertEqual(status, 200)
        return {"X-Token": result["token"]}

    # T1 — роль из заголовка клиента
    def test_t1_client_role_header_does_not_grant_export(self):
        self.assertEqual(self.request("GET", "/admin/export", headers={**self.login(), "X-Role": "staff"})[0], 403)
        self.assertEqual(self.request("GET", "/admin/export", headers={"X-Role": "staff"})[0], 401)

    def test_t1_staff_session_exports_without_header(self):
        status, profiles = self.request("GET", "/admin/export", headers=self.login("staff"))
        self.assertEqual((status, len(profiles)), (200, 2))

    # T2 — IDOR и отсутствие аутентификации
    def test_t2_profile_requires_owner(self):
        self.assertEqual(self.request("GET", "/profile?id=1")[0], 401)
        self.assertEqual(self.request("GET", "/profile?id=2", headers=self.login())[0], 403)

    def test_t2_orders_only_own(self):
        self.assertEqual(self.request("GET", "/orders")[0], 401)
        status, orders = self.request("GET", "/orders", headers=self.login())
        self.assertEqual(status, 200)
        self.assertEqual({o["owner"] for o in orders}, {1})

    def test_t2_files_only_own(self):
        self.assertEqual(self.request("GET", "/files?user=alice&path=receipt.txt")[0], 401)
        self.assertEqual(self.request("GET", "/files?user=bob&path=receipt.txt", headers=self.login())[0], 403)

    # T3 — SQL-инъекция
    def test_t3_profile_id_is_not_sql(self):
        status, result = self.request("GET", "/profile?id=1%20OR%201%3D1", headers=self.login())
        self.assertEqual(status, 400)

    def test_t3_search_is_parameterized_and_staff_only(self):
        self.assertEqual(self.request("GET", "/search?q=%27%20OR%20%271%27%3D%271", headers=self.login())[0], 403)
        status, rows = self.request("GET", "/search?q=%27%20OR%20%271%27%3D%271", headers=self.login("staff"))
        self.assertEqual((status, rows), (200, []))

    # T4 — цена от клиента
    def test_t4_price_comes_from_catalog(self):
        status, order = self.request("POST", "/orders", {"product": "chair", "price": 1}, self.login())
        self.assertEqual((status, order["price"]), (201, 5000))

    # T5 — выход из своего каталога внутри стенда
    def test_t5_files_cannot_reach_private_note(self):
        for path in ("/files?user=../private&path=operator-note.txt", "/files?user=alice&path=../../private/operator-note.txt"):
            with self.subTest(path=path):
                status, body = self.request("GET", path, headers=self.login())
                self.assertIn(status, (400, 403))
                self.assertNotIn("SECRET", str(body))

    # T6 — stored XSS
    def test_t6_reviews_are_escaped(self):
        auth = self.login()
        self.request("POST", "/reviews", {"product": "chair", "text": '<b id="probe">x</b>'}, auth)
        html = self.request("GET", "/reviews/view", headers=auth)[1]
        self.assertNotIn('<b id="probe">', html)
        self.assertIn("&lt;b id=&quot;probe&quot;&gt;", html)

    # T7 — журнал с секретами без аутентификации
    def test_t7_debug_logs_not_public_and_without_secrets(self):
        token = self.login()["X-Token"]
        self.assertIn(self.request("GET", "/debug/logs")[0], (401, 404))
        self.assertIn(self.request("GET", "/debug/logs", headers={"X-Token": token})[0], (403, 404))
        status, logs = self.request("GET", "/debug/logs", headers=self.login("staff"))
        if status == 200:
            self.assertNotIn("learn-alice", str(logs))
            self.assertNotIn(token, str(logs))

    # T8 + T10 — контекст помощника
    def test_t8_t10_context_is_own_order_and_marks_untrusted_reviews(self):
        alice, bob = self.login(), self.login("bob")
        self.request("POST", "/reviews", {"product": "lamp", "text": "bob lamp review"}, bob)
        self.request("POST", "/reviews", {"product": "chair", "text": "alice chair review"}, alice)
        self.assertEqual(self.request("GET", "/assistant/context?order_id=1")[0], 401)
        self.assertEqual(self.request("GET", "/assistant/context?order_id=2", headers=alice)[0], 403)
        status, context = self.request("GET", "/assistant/context?order_id=1", headers=alice)
        self.assertEqual(status, 200)
        prompt = context["prompt"]
        self.assertNotIn("lamp", prompt)
        self.assertIn("alice chair review", prompt)
        self.assertIn("недоверенные", prompt.lower())
        self.assertNotIn("delete_tree", prompt)
        self.assertNotIn("export_profiles", prompt)

    # T9 — избыточные полномочия исполнителя
    def test_t9_execute_requires_session(self):
        decision = {"decision": {"tool": "read_file", "arguments": {"path": "files/alice/receipt.txt"}}}
        self.assertEqual(self.request("POST", "/assistant/execute", decision)[0], 401)

    def test_t9_customer_cannot_run_dangerous_tools(self):
        alice = self.login()
        for decision in (
            {"tool": "read_file", "arguments": {"path": "files/bob/receipt.txt"}},
            {"tool": "read_file", "arguments": {"path": "private/operator-note.txt"}},
            {"tool": "export_profiles", "arguments": {}},
            {"tool": "delete_tree", "arguments": {"path": "files"}},
        ):
            with self.subTest(tool=decision["tool"], args=decision["arguments"]):
                status, body = self.request("POST", "/assistant/execute", {"decision": decision}, alice)
                self.assertEqual(status, 403)
                self.assertNotIn("TEST_BOB", str(body))
        self.assertIn("TEST_BOB", self.shop.sandbox.read("files/bob/receipt.txt"))

    def test_t9_export_profiles_not_available_through_assistant(self):
        # J2 судьи: ПДн выгружаются только прямым /admin/export, помощник — никому
        for who in ("alice", "staff"):
            with self.subTest(who=who):
                status, _ = self.request("POST", "/assistant/execute",
                                         {"decision": {"tool": "export_profiles", "arguments": {}}}, self.login(who))
                self.assertEqual(status, 403)

    def test_t9_delete_tree_not_available_even_for_staff(self):
        status, _ = self.request("POST", "/assistant/execute",
                                 {"decision": {"tool": "delete_tree", "arguments": {"path": "files"}}}, self.login("staff"))
        self.assertEqual(status, 403)
        self.assertIn("TEST_ALICE", self.shop.sandbox.read("files/alice/receipt.txt"))

    # T11 — детали исключений в ответе
    def test_t11_bad_input_has_no_internal_details(self):
        status, body = self.request("POST", "/orders", {}, self.login())
        self.assertEqual(status, 400)
        self.assertNotIn("type", body)
        status, body = self.request("POST", "/assistant/execute", {"decision": "x"}, self.login())
        self.assertEqual(status, 400)

    def test_t11_non_string_fields_are_rejected_not_crashing(self):
        auth = self.login()
        self.assertEqual(self.request("POST", "/login", {"username": ["alice"], "password": "x"})[0], 401)
        self.assertEqual(self.request("POST", "/orders", {"product": ["chair"]}, auth)[0], 400)
        self.assertEqual(self.request("POST", "/reviews", {"product": {"a": 1}, "text": "x"}, auth)[0], 400)

    # T13 — отзыв без аутентификации
    def test_t13_review_requires_session(self):
        self.assertEqual(self.request("POST", "/reviews", {"product": "chair", "text": "spam"})[0], 401)
        self.assertEqual(self.request("POST", "/reviews", {"product": "sofa", "text": "x"}, self.login())[0], 400)


class HttpHeadersSecurityTest(unittest.TestCase):
    """T15 (CORS/CSRF) и T16 (clickjacking, CSP) — на уровне HTTP-транспорта."""

    @classmethod
    def setUpClass(cls):
        cls.shop = Shop()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cls.shop))
        cls.server.daemon_threads = True
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        cls.server.server_close()
        cls.shop.close()

    def call(self, method, path, body=None, headers=None):
        data = json.dumps(body).encode() if body is not None else None
        request = Request(self.base + path, data=data, method=method,
                          headers={"Content-Type": "application/json", **(headers or {})})
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, response.headers, response.read().decode()

    def token(self):
        return json.loads(self.call("POST", "/login", {"username": "alice", "password": "learn-alice"})[2])["token"]

    def test_t15_no_cors_headers_so_cross_site_requests_cannot_use_token(self):
        _, headers, _ = self.call("GET", "/orders", headers={"X-Token": self.token(), "Origin": "https://evil.example"})
        self.assertIsNone(headers.get("Access-Control-Allow-Origin"))
        self.assertIsNone(headers.get("Set-Cookie"))

    def test_t16_html_cannot_be_framed_and_has_csp(self):
        status, headers, _ = self.call("GET", "/reviews/view", headers={"X-Token": self.token()})
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("X-Frame-Options"), "DENY")
        self.assertIn("default-src 'none'", headers.get("Content-Security-Policy", ""))
        self.assertIn("frame-ancestors 'none'", headers.get("Content-Security-Policy", ""))
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")


if __name__ == "__main__":
    unittest.main()
