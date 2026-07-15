import time, threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright

DOCS = "/home/vasis/projects_hobby/pinball-soccer-98/docs"
OUT = "/home/vasis/projects_hobby/pinball-soccer-98/tools"
PORT = 8225
Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DOCS)
httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
httpd.allow_reuse_address = True
threading.Thread(target=httpd.serve_forever, daemon=True).start()
print(f"serving on :{PORT}")

def canvas_hash(pg):
    return pg.evaluate("""() => {
      const c = document.querySelector('#screen canvas');
      const d = c.getContext('2d').getImageData(0,0,c.width,c.height).data;
      let h = 2166136261 >>> 0;
      for (let i=0;i<d.length;i+=613){ h ^= d[i]; h = Math.imul(h,16777619) >>> 0; }
      return h;
    }""")

# Drive a HELD touch at a guest-logical coordinate (640x480 space).
def touch_go(pg, gx, gy, hold=0.6):
    pg.evaluate("""([gx,gy]) => {
      const c = document.querySelector('#screen canvas');
      const r = c.getBoundingClientRect();
      const cx = r.left + gx*r.width/640, cy = r.top + gy*r.height/480;
      window.__t = (type,phase) => {
        const t = new Touch({identifier:1,target:c,clientX:cx,clientY:cy});
        c.dispatchEvent(new TouchEvent(type,{changedTouches:[t],touches:phase==='end'?[]:[t],bubbles:true,cancelable:true}));
      };
      window.__t('touchstart','start');
    }""", [gx, gy])
    time.sleep(hold)
    pg.evaluate("window.__t('touchend','end')")

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=[
        "--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
    ctx = b.new_context(viewport={"width": 393, "height": 851},
                        is_mobile=True, has_touch=True)
    pg = ctx.new_page()
    pg.goto(f"http://127.0.0.1:{PORT}/index.html")
    for _ in range(120):
        if pg.eval_on_selector_all("#screen canvas", "e=>e.length"):
            break
        time.sleep(1)
    print("canvas mounted; settling language screen…")
    time.sleep(35)

    pg.screenshot(path=f"{OUT}/tgo_0_before.png")
    h0 = canvas_hash(pg)
    # Sanity: is the screen static right now? (attract could animate)
    time.sleep(2); h0b = canvas_hash(pg)
    print(f"before: hash={h0} (static-check {h0b}, {'STATIC' if h0==h0b else 'animating'})")

    print("tap GO (315,347) held…")
    touch_go(pg, 315, 347, hold=0.6)
    time.sleep(12)

    pg.screenshot(path=f"{OUT}/tgo_1_after.png")
    h1 = canvas_hash(pg)
    print(f"after:  hash={h1}")
    changed = h1 != h0 and h1 != h0b
    print("screen changed after GO tap:", changed)
    print("RESULT:", "PASS" if changed else "FAIL")
    b.close()
httpd.shutdown()
