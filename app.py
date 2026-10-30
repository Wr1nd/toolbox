"""Private, temporary-file utility workbench."""
import base64
import hashlib
from pathlib import Path
from urllib.parse import quote, unquote
from fastapi import FastAPI, Form, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse
from starlette.background import BackgroundTask
import io, os, re, socket, ipaddress, subprocess, tempfile, shutil, zipfile, threading
from urllib.parse import urlsplit
from PIL import Image, ImageOps, UnidentifiedImageError
from pypdf import PdfReader, PdfWriter
import qrcode

LIMIT = 100 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 25_000_000
WORK = threading.BoundedSemaphore(2)
ALLOWED_HOSTS = {'192.168.31.150:5082', '127.0.0.1:5082', 'localhost:5082'}

def public_target(url):
    try:
        u = urlsplit(url)
        if u.scheme not in ('http','https') or not u.hostname or u.username or u.password or u.port not in (None,80,443):
            raise ValueError('Use a public HTTP or HTTPS URL on a standard port.')
        addresses = socket.getaddrinfo(u.hostname, u.port or (443 if u.scheme == 'https' else 80), type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
            raise ValueError('Private, loopback and reserved addresses are not allowed.')
        return addresses[0][4][0]
    except (ValueError, OSError) as exc:
        raise ValueError(str(exc)) from exc

def result_file(directory, path, media_type=None):
    return FileResponse(path, filename=path.name, media_type=media_type, background=BackgroundTask(shutil.rmtree,directory,True))

def acquire():
    if not WORK.acquire(blocking=False): raise HTTPException(429,'Two tasks are already running. Please try again shortly.')

async def upload(file):
    data = await file.read(LIMIT+1)
    if len(data)>LIMIT: raise HTTPException(413,'Maximum total upload is 100 MB.')
    return data
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title='Text Box', docs_url=None, redoc_url=None)

@app.post('/api/text')
def text_tool(operation: str = Form(...), text: str = Form('')):
    try:
        if operation in ('md5','sha256','sha512'):
            result = hashlib.new(operation, text.encode()).hexdigest()
        elif operation == 'base64_encode': result = base64.b64encode(text.encode()).decode()
        elif operation == 'base64_decode': result = base64.b64decode(text, validate=True).decode('utf-8')
        elif operation == 'url_encode': result = quote(text, safe='')
        elif operation == 'url_decode': result = unquote(text, errors='strict')
        else: raise ValueError('Unknown operation')
        return {'result': result}
    except (ValueError, UnicodeError) as exc:
        raise HTTPException(400, str(exc)) from exc

# Register utility routes after shared application helpers are defined.
import tools  # noqa: E402,F401

