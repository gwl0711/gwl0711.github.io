"""Browser smoke checks for the static site. Run from any working directory."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlparse, unquote
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
OUTPUT = ROOT / "test-results"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def main():
    OUTPUT.mkdir(exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(SITE)))
    Thread(target=server.serve_forever, daemon=True).start()
    origin = f"http://127.0.0.1:{server.server_port}"
    errors, failures, report = [], [], []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(permissions=["clipboard-read", "clipboard-write"])
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("response", lambda response: failures.append(f"{response.status}: {response.url}") if response.status >= 400 else None)
            for width, height in [(1440, 1000), (1024, 900), (768, 1024), (390, 844), (320, 740)]:
                page.set_viewport_size({"width": width, "height": height})
                page.goto(origin, wait_until="networkidle")
                assert page.locator("h1").inner_text().startswith("Gyuwon Lee")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Horizontal overflow at {width}px"
                broken_images = page.locator("img").evaluate_all("images => images.filter(i => !i.complete || !i.naturalWidth).map(i => i.src)")
                assert not broken_images, broken_images
                if width in (1440, 390):
                    page.screenshot(path=str(OUTPUT / f"homepage-{width}.png"), full_page=True)
                report.append(f"Layout and images: {width}px passed")

            # Validate actual site links, including fragments and every download.
            for href in set(page.locator("a[href]").evaluate_all("links => links.map(a => a.getAttribute('href'))")):
                parsed = urlparse(href)
                if parsed.scheme or href == "#":
                    continue
                if parsed.path:
                    target = (SITE / unquote(parsed.path)).resolve()
                    assert target.is_relative_to(SITE) and target.exists(), f"Missing local link: {href}"
                    response = page.request.get(f"{origin}/{parsed.path}")
                    assert response.ok, href
                elif parsed.fragment:
                    assert page.locator(f"[id='{parsed.fragment}']").count() == 1, href
            report.append("Local destinations and downloads passed")

            page.set_viewport_size({"width": 390, "height": 844})
            page.get_by_role("button", name="Share this page").click()
            assert page.locator("#share-dialog").is_visible()
            page.get_by_role("button", name="Copy link").click()
            assert page.evaluate("navigator.clipboard.readText()") == "https://gwl0711.github.io/"
            page.keyboard.press("Escape")
            assert not page.locator("#share-dialog").is_visible()
            assert page.get_by_role("button", name="Share this page").evaluate("e => e === document.activeElement")
            page.locator("#copy-email").click()
            assert page.evaluate("navigator.clipboard.readText()") == "gwl0711@gmail.com"
            assert page.locator("#toast").inner_text() == "Email address copied"
            report.append("Share dialog, Escape/focus return, and clipboard passed")

            page.goto(f"{origin}/qr.html", wait_until="networkidle")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert page.get_by_role("link", name="Print PDF").get_attribute("download") == ""
            page.screenshot(path=str(OUTPUT / "qr-mobile.png"), full_page=True)
            report.append("QR download page passed")

            no_js = browser.new_context(java_script_enabled=False, viewport={"width": 390, "height": 844})
            basic = no_js.new_page()
            basic.goto(origin)
            assert basic.locator(".publication").count() == 4
            assert basic.get_by_role("link", name="View CV").is_visible()
            assert basic.get_by_role("link", name="Get in touch").is_visible()
            assert not basic.get_by_role("button", name="Share this page").is_visible()
            report.append("Core content and links work without JavaScript")
            assert not errors, errors
            assert not failures, failures
            browser.close()
        try:
            import cv2
            decoded, _points, _ = cv2.QRCodeDetector().detectAndDecode(cv2.imread(str(SITE / "assets" / "qr-code.png")))
            assert decoded == "https://gwl0711.github.io/", f"QR decode mismatch: {decoded}"
            report.append("Generated PNG independently decoded to the correct HTTPS URL")
        except ImportError:
            report.append("OpenCV unavailable: independently scan the generated QR before printing")
        print(json.dumps({"status": "passed", "checks": report}, indent=2))
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
