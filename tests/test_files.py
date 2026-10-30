import io, zipfile
import pytest
from PIL import Image
from pypdf import PdfWriter, PdfReader
from fastapi.testclient import TestClient
from app import app

@pytest.fixture
def client():
    with TestClient(app,base_url='http://192.168.31.150:5082') as c: yield c

def pdf():
    w=PdfWriter(); w.add_blank_page(200,200); b=io.BytesIO(); w.write(b); return b.getvalue()

def test_pdf_merge(client):
    r=client.post('/api/pdf', data={'operation':'merge'},files=[('files',('a.pdf',pdf())),('files',('b.pdf',pdf()))])
    assert r.status_code==200
    assert len(PdfReader(io.BytesIO(r.content)).pages)==2

def test_pdf_split(client):
    r=client.post('/api/pdf',data={'operation':'split'},files={'files':('a.pdf',pdf())})
    assert r.status_code==200
    assert len(zipfile.ZipFile(io.BytesIO(r.content)).namelist())==1

def test_pdf_compress(client):
    r=client.post('/api/pdf',data={'operation':'compress'},files={'files':('a.pdf',pdf())})
    assert r.status_code==200
    assert len(PdfReader(io.BytesIO(r.content)).pages)==1

def test_image(client):
    b=io.BytesIO(); Image.new('RGB',(80,40),'red').save(b,'PNG')
    r=client.post('/api/image',data={'format':'webp','width':'20','quality':'80'},files={'file':('x.png',b.getvalue())})
    assert r.status_code==200
    assert Image.open(io.BytesIO(r.content)).size==(20,10)

def test_qr(client):
    r=client.post('/api/qr',data={'text':'hello','foreground':'#123456','background':'#ffffff','size':'256'})
    assert r.status_code==200
    assert Image.open(io.BytesIO(r.content)).size==(256,256)

@pytest.mark.parametrize('url',['http://127.0.0.1','http://192.168.31.150','file:///etc/passwd','http://[::1]','http://169.254.169.254'])
def test_screenshot_blocks_private(client,url):
    assert client.post('/api/screenshot',data={'url':url}).status_code==400

def test_youtube_rejects_other_hosts(client):
    assert client.post('/api/youtube',data={'url':'http://127.0.0.1','format':'mp4'}).status_code==400

def test_cross_origin_blocked(client):
    assert client.post('/api/text',data={'operation':'md5','text':'x'},headers={'Origin':'https://evil.example'}).status_code==403

def test_invalid_base64(client):
    assert client.post('/api/text',data={'operation':'base64_decode','text':'%%%'}).status_code==400
