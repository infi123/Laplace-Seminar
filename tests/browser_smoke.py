"""Optional test for standalone HTML in an actual Chromium browser.
Run: python tests/browser_smoke.py
"""
import asyncio
from pathlib import Path
from threading import Thread
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]

async def run():
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(ROOT/"dist")))
    Thread(target=server.serve_forever,daemon=True).start()
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
        page=await browser.new_page(viewport={'width':1440,'height':900})
        errors=[]
        page.on('pageerror',lambda exc:errors.append(str(exc)))
        await page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
        await page.wait_for_function('document.querySelector("#slide").complete && document.querySelector("#slide").naturalWidth>0')
        print('Initial slide:',await page.locator('#count').inner_text())
        for n in [6,8,21,23,27,29]:
            await page.evaluate('''(i)=> {page=i; show();}''',n)
            await page.wait_for_function('document.querySelector("#video").readyState>=2',timeout=15000)
            await page.wait_for_timeout(500)
            vid=await page.evaluate('''() => ({time:document.querySelector("#video").currentTime,
                   size:[document.querySelector("#video").videoWidth,document.querySelector("#video").videoHeight],
                   visible:document.querySelector("#screen").classList.contains("is-video")})''')
            print(n,vid)
            assert vid['size']==[1134,638] and vid['visible'],f'Broken video on {n}: {vid}'
            if n in [21,23,27,29,6]:
                await page.screenshot(path=str(ROOT/'qa'/f'browser_{n:02d}.png'))
        assert not errors,errors
        await browser.close()
        server.shutdown()
        print('Browser smoke test passed')

if __name__=='__main__':asyncio.run(run())
