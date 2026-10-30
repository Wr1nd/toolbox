"""One-shot Chromium capture through a public-IP-only, DNS-pinned proxy."""
import asyncio
import contextlib
import sys
from urllib.parse import urlsplit
from app import public_target
from playwright.async_api import async_playwright

async def proxy(reader, writer):
    upstream=None
    try:
        header=await asyncio.wait_for(reader.readuntil(b'\r\n\r\n'),10)
        method,target,version=header.split(b'\r\n',1)[0].decode().split(' ',2)
        if method=='CONNECT':
            url='https://'+target
            parsed=urlsplit(url)
        else:
            url=target; parsed=urlsplit(url)
        address=await asyncio.to_thread(public_target,url)
        remote,upstream=await asyncio.wait_for(asyncio.open_connection(address,parsed.port or (443 if parsed.scheme=='https' else 80)),10)
        if method=='CONNECT':
            writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
        else:
            path=parsed.path or '/'
            if parsed.query: path+='?'+parsed.query
            lines=header.split(b'\r\n')[1:]
            lines=[line for line in lines if not line.lower().startswith((b'proxy-',b'connection:'))]
            upstream.write(f'{method} {path} {version}\r\n'.encode()+b'\r\n'.join(lines))
            await upstream.drain()
        await writer.drain()
        async def pump(src,dst):
            while chunk:=await src.read(65536):
                dst.write(chunk); await dst.drain()
        tasks=[asyncio.create_task(pump(reader,upstream)),asyncio.create_task(pump(remote,writer))]
        done,pending=await asyncio.wait(tasks,timeout=55,return_when=asyncio.FIRST_COMPLETED)
        for task in pending: task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
    except Exception:
        with contextlib.suppress(Exception):
            writer.write(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n'); await writer.drain()
    finally:
        writer.close()
        if upstream: upstream.close()

async def main():
    server=await asyncio.start_server(proxy,'127.0.0.1',0,limit=65536)
    async with server, async_playwright() as p:
        port=server.sockets[0].getsockname()[1]
        browser=await p.chromium.launch(headless=True,proxy={'server':f'http://127.0.0.1:{port}','bypass':'<-loopback>'},args=['--disable-quic','--force-webrtc-ip-handling-policy=disable_non_proxied_udp'])
        try:
            page=await browser.new_page(viewport={'width':int(sys.argv[2]),'height':900},service_workers='block',accept_downloads=False)
            await page.route('**/*',lambda route: route.abort() if urlsplit(route.request.url).scheme not in ('http','https') else route.continue_())
            await page.goto(sys.argv[1],wait_until='domcontentloaded',timeout=35000)
            with contextlib.suppress(Exception): await page.wait_for_load_state('networkidle',timeout=5000)
            height=await page.evaluate('Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)')
            if height>20000: raise ValueError('Page exceeds 20,000px capture limit')
            await page.screenshot(path=sys.argv[3],full_page=True,timeout=15000,animations='disabled')
        finally: await browser.close()

if __name__=='__main__': asyncio.run(main())
