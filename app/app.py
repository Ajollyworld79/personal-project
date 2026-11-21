import os
import sys

# Ensure project root in path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from quart import Quart, request

from app import chat, client, live, pages

app = Quart(
    __name__,
    template_folder=os.path.join(PROJECT_ROOT, "templates"),
    static_folder=os.path.join(PROJECT_ROOT, "static"),
)
# The only request bodies are small JSON chat questions.
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
app.register_blueprint(pages.bp)
app.register_blueprint(chat.bp)
app.register_blueprint(live.bp)


@app.after_serving
async def _close_http() -> None:
    await client.close()


# Everything the site loads: own assets, YouTube thumbnails and the
# privacy-enhanced YouTube player. Inline style attributes come from React.
_CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https://i.ytimg.com",
    "font-src 'self' data:",
    "connect-src 'self'",
    "frame-src https://www.youtube-nocookie.com",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])


@app.after_request
async def _security_headers(response):
    headers = response.headers
    # The Vite dev server injects inline module scripts, so CSP is production-only.
    if not os.environ.get("VITE_DEV_SERVER"):
        headers.setdefault("Content-Security-Policy", _CSP)
    headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    headers.setdefault("X-Content-Type-Options", "nosniff")
    headers.setdefault("X-Frame-Options", "DENY")
    headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    # Vite output carries a content hash in the filename, so it never changes.
    if request.path.startswith("/static/dist/assets/"):
        headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.app:app", host="127.0.0.1", port=8000, reload=True)
