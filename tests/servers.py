"""Loopback fake provider servers shared by pytest adapter tests and BDD scenarios.

Each is a generator: advance once to start the server and receive it; exhaust it
(or close it) to stop. They bind only to 127.0.0.1 and need no key or download.
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread

import jsonschema

from reason_commons.adapters.anthropic import DEFAULT_MODEL
from tests.support import bounded_case


def anthropic_server_instance():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, value, status=200, headers=None):
            body = value if isinstance(value, bytes) else json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Length", str(len(body)))
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            self.server.requests.append(("GET", self.path, dict(self.headers), None))
            if self.server.get_status != 200:
                self.respond({"error": "fixture-secret: unsafe server body"}, self.server.get_status)
            else:
                self.respond({"id": DEFAULT_MODEL, "max_input_tokens": 1000000})

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.server.requests.append(("POST", self.path, dict(self.headers), payload))
            if self.path == "/v1/messages/count_tokens":
                self.respond({"input_tokens": 12345})
                return
            if self.server.custom is not None:
                self.respond(*self.server.custom)
                return
            request = json.loads(payload["messages"][0]["content"])
            proposal = bounded_case(request)
            for i, update in enumerate(proposal["proposed_updates"]):
                update.setdefault("temporary_id", f"temp_update_{i}")
            jsonschema.validate(proposal, payload["tools"][0]["input_schema"])
            response = {"model": payload["model"], "stop_reason": "tool_use", "content": [
                {"type": "tool_use", "name": "submit_proposal", "id": "fixture-call", "input": proposal}]}
            if self.server.transform:
                self.server.transform(response)
            self.respond(response)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.requests, server.custom, server.transform, server.get_status = [], None, None, 200
    server.url = f"http://127.0.0.1:{server.server_port}/v1"
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def lm_studio_server_instance():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, body, status=200, headers=None):
            content = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self):
            self.server.requests.append(("GET", self.path, dict(self.headers), None))
            self.respond({"data": [{"id": model} for model in self.server.models]})

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.server.requests.append(("POST", self.path, dict(self.headers), body))
            request = json.loads(body["messages"][1]["content"])
            if self.server.custom is not None:
                content, *rest = self.server.custom
                if isinstance(content, dict) and "choices" in content:
                    content = {"model": body["model"], **content}
                self.respond(content, *rest)
                return
            result = self.server.author(request)
            for index, update in enumerate(result["proposed_updates"]):
                # The real provider grammar requires named updates. The domain
                # and provider-free BDD also accept unnamed updates.
                update.setdefault("temporary_id", f"temp_update_{index}")
            jsonschema.validate(result, body["response_format"]["json_schema"]["schema"])
            self.respond({"model": self.server.response_model or body["model"],
                          "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(result)}}]})

    instance = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    instance.requests, instance.models, instance.custom = [], ["model", "selected-model", "model-a", "model-b"], None
    instance.response_model = None
    instance.author = bounded_case
    instance.url = f"http://127.0.0.1:{instance.server_port}/v1"
    thread = Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    yield instance
    instance.shutdown()
    instance.server_close()
    thread.join(timeout=2)
