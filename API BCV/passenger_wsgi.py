import asyncio
import os
import sys
from http import HTTPStatus

BASE_DIR = os.path.dirname(__file__)
if BASE_DIR not in sys.path:
	sys.path.insert(0, BASE_DIR)


def _error_application(message):
	payload = message.encode("utf-8", errors="replace")

	def _app(environ, start_response):
		start_response(
			"500 Internal Server Error",
			[
				("Content-Type", "text/plain; charset=utf-8"),
				("Content-Length", str(len(payload))),
			],
		)
		return [payload]

	return _app


try:
	from app.main import app as asgi_app

	def application(environ, start_response):
		scope = {
			"type": "http",
			"asgi": {"version": "3.0"},
			"http_version": "1.1",
			"method": environ.get("REQUEST_METHOD", "GET"),
			"headers": [
				(name.lower().encode(), value.encode())
				for name, value in (
					(k[5:].replace("_", "-"), environ[k])
					for k in environ
					if k.startswith("HTTP_")
				)
			],
			"path": environ.get("PATH_INFO", "/") or "/",
			"query_string": environ.get("QUERY_STRING", "").encode(),
			"root_path": environ.get("SCRIPT_NAME", ""),
			"server": (
				environ.get("SERVER_NAME", "localhost"),
				int(environ.get("SERVER_PORT", "80")),
			),
			"scheme": environ.get("wsgi.url_scheme", "http"),
			"client": (environ.get("REMOTE_ADDR", ""), 0),
		}

		body = environ["wsgi.input"].read()
		response = {"status": 500, "headers": [], "body": b""}

		async def receive():
			return {"type": "http.request", "body": body, "more_body": False}

		async def send(message):
			if message["type"] == "http.response.start":
				response["status"] = message["status"]
				response["headers"] = message.get("headers", [])
			elif message["type"] == "http.response.body":
				response["body"] += message.get("body", b"")

		async def run_app():
			await asgi_app(scope, receive, send)

		asyncio.run(run_app())

		status_code = int(response.get("status", 500))
		reason = HTTPStatus(status_code).phrase if status_code in HTTPStatus._value2member_map_ else "OK"
		status_line = f"{status_code} {reason}"
		headers = [(k.decode(), v.decode()) for k, v in response.get("headers", [])]
		start_response(status_line, headers)
		return [response.get("body", b"")]

except Exception as exc:
	application = _error_application(f"Error: {exc.__class__.__name__}: {exc}")
