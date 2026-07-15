import threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright

DOCS = "/home/vasis/projects_hobby/pinball-soccer-98/docs"
PORT = 8223
Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DOCS)
httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
httpd.allow_reuse_address = True
threading.Thread(target=httpd.serve_forever, daemon=True).start()
print(f"serving on :{PORT}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=[
        "--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
    ctx = browser.new_context(viewport={"width": 393, "height": 851},
                              is_mobile=True, has_touch=True)
    page = ctx.new_page()
    page.goto(f"http://127.0.0.1:{PORT}/index.html")

    for i in range(120):
        if page.eval_on_selector_all("#screen canvas", "e=>e.length"):
            break
        page.wait_for_timeout(1000)
    else:
        print("RESULT: FAIL (no canvas)"); browser.close(); httpd.shutdown(); raise SystemExit

    # Record the corrected (__rwFixed) events actually forwarded to the guest.
    page.evaluate("""
      window.__fwd = [];
      const c = document.querySelector('#screen canvas');
      c.addEventListener('mousedown', e => e.__rwFixed && window.__fwd.push({t:e.type,x:Math.round(e.offsetX),y:Math.round(e.offsetY),ts:performance.now()}), true);
      c.addEventListener('mouseup',   e => e.__rwFixed && window.__fwd.push({t:e.type,x:Math.round(e.offsetX),y:Math.round(e.offsetY),ts:performance.now()}), true);
      c.addEventListener('mousemove', e => e.__rwFixed && window.__fwd.push({t:e.type,x:Math.round(e.offsetX),y:Math.round(e.offsetY),ts:performance.now()}), true);
      window.__logsize = [c.width/(devicePixelRatio||1), c.height/(devicePixelRatio||1)];
    """)

    # Dispatch a HELD touch at the displayed centre: touchstart, hold, touchend.
    page.evaluate("""
      const c = document.querySelector('#screen canvas');
      const r = c.getBoundingClientRect();
      window.__cx = r.left + r.width/2; window.__cy = r.top + r.height/2;
      window.__touch = (type, phase) => {
        const t = new Touch({identifier:1, target:c, clientX:window.__cx, clientY:window.__cy});
        c.dispatchEvent(new TouchEvent(type, {changedTouches:[t], touches: phase==='end'?[]:[t], bubbles:true, cancelable:true}));
      };
      window.__touch('touchstart','start');
    """)
    page.wait_for_timeout(400)  # hold across several frames
    page.evaluate("window.__touch('touchend','end')")
    page.wait_for_timeout(100)

    fwd = page.evaluate("window.__fwd")
    logw, logh = page.evaluate("window.__logsize")
    print("logical canvas:", logw, "x", logh)
    for e in fwd:
        print(f"  {e['t']:10s} ({e['x']},{e['y']}) @{e['ts']:.0f}ms")

    downs = [e for e in fwd if e["t"] == "mousedown"]
    ups = [e for e in fwd if e["t"] == "mouseup"]
    ok = False
    if downs and ups:
        d, u = downs[0], ups[-1]
        gap = u["ts"] - d["ts"]
        coord_ok = abs(d["x"] - logw/2) <= 8 and abs(d["y"] - logh/2) <= 8
        held = gap >= 300
        print(f"down=({d['x']},{d['y']}) up=({u['x']},{u['y']}) held={gap:.0f}ms coord_ok={coord_ok}")
        ok = coord_ok and held
    print("RESULT:", "PASS" if ok else "FAIL")
    browser.close()
httpd.shutdown()
