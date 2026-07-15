import threading, http.server, socketserver, functools, json
from playwright.sync_api import sync_playwright

DOCS = "/home/vasis/projects_hobby/pinball-soccer-98/docs"
OUT = "/home/vasis/projects_hobby/pinball-soccer-98/tools"
PORT = 8211

Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DOCS)
httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
httpd.allow_reuse_address = True
threading.Thread(target=httpd.serve_forever, daemon=True).start()
print(f"serving {DOCS} on :{PORT}")

EXPECT = {"KeyZ", "ShiftRight", "Enter", "Space"}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    # Emulate a phone: touch + coarse pointer.
    ctx = browser.new_context(
        viewport={"width": 393, "height": 851},
        is_mobile=True, has_touch=True,
    )
    page = ctx.new_page()
    page.goto(f"http://127.0.0.1:{PORT}/index.html")

    # Record every keyboard event that reaches window (what the game listens on).
    page.evaluate("""
      window.__keys = [];
      window.addEventListener('keydown', e => window.__keys.push(['down', e.code]), true);
      window.addEventListener('keyup',   e => window.__keys.push(['up',   e.code]), true);
    """)

    coarse = page.evaluate("matchMedia('(pointer: coarse)').matches")
    has_touch_cls = page.evaluate("document.body.classList.contains('touch')")
    pad_disp = page.eval_on_selector("#touchpad", "el => getComputedStyle(el).display")
    n_btns = page.eval_on_selector_all(".tbtn", "els => els.length")
    print(f"pointer:coarse={coarse}  body.touch={has_touch_cls}  #touchpad.display={pad_disp}  buttons={n_btns}")

    # Tap each button and confirm it emits the matching keydown+keyup on window.
    results = {}
    for code in ["KeyZ", "Enter", "Space", "ShiftRight"]:
        page.evaluate("window.__keys = []")
        page.tap(f'.tbtn[data-code="{code}"]')
        page.wait_for_timeout(120)
        keys = page.evaluate("window.__keys")
        results[code] = keys
        print(f"  tap {code:10s} -> {keys}")

    page.screenshot(path=f"{OUT}/touch_pad.png")

    ok = (
        has_touch_cls and pad_disp == "flex" and n_btns == 4 and
        all(
            results[c] == [["down", c], ["up", c]]
            for c in ["KeyZ", "Enter", "Space", "ShiftRight"]
        )
    )
    print("RESULT:", "PASS" if ok else "FAIL")
    browser.close()
httpd.shutdown()
