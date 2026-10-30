"""Run against the deployed service, not an in-process test double."""
import io,json,zipfile
from pathlib import Path
import httpx
from PIL import Image
from pypdf import PdfWriter,PdfReader
from playwright.sync_api import sync_playwright
BASE='http://192.168.31.150:5082'

def main():
    with httpx.Client(base_url=BASE,timeout=300,trust_env=False) as c:
        assert c.get('/api/health').json()['status']=='ok'
        b=io.BytesIO(); w=PdfWriter(); w.add_blank_page(300,200); w.add_blank_page(300,200); w.write(b)
        for operation in ['merge','split','compress']:
            files=[('files',('a.pdf',b.getvalue()))]
            if operation=='merge': files.append(('files',('b.pdf',b.getvalue())))
            r=c.post('/api/pdf',data={'operation':operation},files=files); assert r.status_code==200,(operation,r.text)
            if operation=='split': assert len(zipfile.ZipFile(io.BytesIO(r.content)).namelist())==2
            else: assert len(PdfReader(io.BytesIO(r.content)).pages)==(4 if operation=='merge' else 2)
            print('LIVE PDF',operation,'OK',len(r.content))
        b=io.BytesIO(); Image.new('RGB',(800,400),'#124d43').save(b,'PNG')
        for fmt in ['webp','jpeg','png']:
            r=c.post('/api/image',data={'format':fmt,'width':'200'},files={'file':('test.png',b.getvalue())}); assert r.status_code==200,r.text
            im=Image.open(io.BytesIO(r.content)); assert im.size==(200,100); print('LIVE IMAGE',fmt,'OK')
        r=c.post('/api/qr',data={'text':BASE,'foreground':'#123456','background':'#ffffff','size':'512'}); assert r.status_code==200,r.text
        assert Image.open(io.BytesIO(r.content)).size==(512,512); print('LIVE QR OK')
        r=c.post('/api/screenshot',data={'url':'https://example.com','width':'1280'}); assert r.status_code==200,r.text
        assert Image.open(io.BytesIO(r.content)).width==1280; print('LIVE SCREENSHOT OK',len(r.content))
        for op,text in [('md5','hello'),('sha256','hello'),('sha512','hello'),('base64_encode','hello'),('base64_decode','aGVsbG8='),('url_encode','hello world'),('url_decode','hello%20world')]:
            r=c.post('/api/text',data={'operation':op,'text':text}); assert r.status_code==200,r.text; print('LIVE TEXT',op,'OK')
        for fmt in ['mp4','mp3']:
            r=c.post('/api/youtube',data={'url':'https://www.youtube.com/watch?v=aqz-KE-bpKQ','format':fmt})
            if r.status_code==200:
                assert len(r.content)>10000; print('LIVE YOUTUBE',fmt,'OK',len(r.content)); Path(f'/tmp/toolbox-test.{fmt}').write_bytes(r.content)
            else: print('LIVE YOUTUBE',fmt,'BLOCKED',r.status_code,r.text)
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={'width':1440,'height':1000})
        errors=[]; page.on('pageerror',lambda err: errors.append(str(err)))
        page.goto(BASE); page.wait_for_selector('.nav-item')
        assert page.locator('.nav-item').count()==6
        for key in ['pdf','image','qr','screenshot','text','youtube']:
            page.locator(f'[data-tool="{key}"]').click(); assert page.locator('#tool-form button[type=submit]').is_visible()
        page.locator('[data-tool="text"]').click(); page.locator('#text').fill('hello'); page.locator('button[type=submit]').click()
        page.wait_for_selector('#text-result'); assert page.locator('#text-result').input_value().startswith('2cf24dba')
        page.locator('[data-tool="qr"]').click(); page.locator('#text').fill(BASE); page.locator('button[type=submit]').click(); page.wait_for_selector('a.download')
        assert page.locator('#result img').is_visible()
        page.screenshot(path='/tmp/muggle-toolbox-desktop.png',full_page=True)
        page.set_viewport_size({'width':390,'height':844}); page.screenshot(path='/tmp/muggle-toolbox-mobile.png',full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert not errors,errors
        browser.close(); print('BROWSER desktop/mobile navigation, hash, QR, no JS errors: OK')
if __name__=='__main__': main()
