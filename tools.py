from app import *
import asyncio
from fastapi.concurrency import run_in_threadpool
from contextlib import contextmanager

@contextmanager
def job():
    acquire()
    directory = tempfile.mkdtemp(prefix='toolbox-')
    try:
        yield directory, Path(directory)
    except Exception:
        shutil.rmtree(directory,ignore_errors=True)
        raise
    finally:
        WORK.release()

@app.middleware('http')
async def guard(request, call_next):
    host=request.headers.get('host','')
    if host not in ALLOWED_HOSTS:
        return JSONResponse({'detail':'Unknown host'},400)
    origin=request.headers.get('origin')
    if request.method=='POST' and ((origin and origin != f'http://{host}') or request.headers.get('sec-fetch-site')=='cross-site'):
        return JSONResponse({'detail':'Cross-origin requests are not allowed.'},403)
    try:
        if int(request.headers.get('content-length','0'))>LIMIT:
            return JSONResponse({'detail':'Maximum total upload is 100 MB.'},413)
    except ValueError: return JSONResponse({'detail':'Invalid content length'},400)
    if request.method=='POST':
        # Bound streamed and chunked bodies before multipart parsing writes to disk.
        body=bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body)>LIMIT: return JSONResponse({'detail':'Maximum total upload is 100 MB.'},413)
        request._body=bytes(body)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Cache-Control']='no-store'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' blob:; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    return response

@app.get('/api/health')
def health(): return {'status':'ok','tools':6}

@app.exception_handler(ValueError)
async def bad_value(request, exc): return JSONResponse({'detail':str(exc)},400)

@app.post('/api/pdf')
def pdf_tool(operation: str=Form(...),files: list[UploadFile]=File(...),pages: str=Form('')):
    if not 1<=len(files)<=20: raise ValueError('Choose 1–20 PDFs.')
    if operation not in ('merge','split','compress'): raise ValueError('Unknown PDF operation.')
    if operation!='merge' and len(files)!=1: raise ValueError('Choose exactly one PDF.')
    with job() as (directory,root):
        try:
            readers=[PdfReader(f.file) for f in files]
            if any(r.is_encrypted for r in readers): raise ValueError('Password-protected PDFs are not supported.')
            if sum(len(r.pages) for r in readers)>500: raise ValueError('Maximum 500 pages per task.')
            writer=PdfWriter()
            if operation=='split':
                reader=readers[0]
                if pages.strip():
                    selected=[]
                    for part in pages.split(','):
                        if not re.fullmatch(r'\s*\d+(?:-\d+)?\s*',part): raise ValueError('Use page numbers such as 1-3,5.')
                        ends=[int(x) for x in part.strip().split('-')]
                        start,end=ends[0],ends[-1]
                        if start<1 or end<start or end>len(reader.pages): raise ValueError('Page range is outside the document.')
                        selected.extend(range(start-1,end))
                    if len(selected)>500: raise ValueError('Maximum 500 selected pages.')
                    for n in selected: writer.add_page(reader.pages[n])
                    output=root/'selected-pages.pdf'; writer.write(output)
                else:
                    output=root/'split-pages.zip'
                    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
                        for n,page in enumerate(reader.pages,1):
                            w=PdfWriter(); w.add_page(page); b=io.BytesIO(); w.write(b); z.writestr(f'page-{n:03}.pdf',b.getvalue())
            else:
                for reader in readers:
                    for page in reader.pages: writer.add_page(page)
                if operation=='compress':
                    for page in writer.pages: page.compress_content_streams()
                    writer.compress_identical_objects(remove_duplicates=True,remove_unreferenced=True)
                output=root/('merged.pdf' if operation=='merge' else 'compressed.pdf'); writer.write(output)
                if operation=='compress':
                    files[0].file.seek(0); original=files[0].file.read()
                    if len(original)<output.stat().st_size: output.write_bytes(original)
            return result_file(directory,output)
        except ValueError: raise
        except Exception as exc: raise ValueError('Could not process this PDF. Check that it is valid and unencrypted.') from exc

@app.post('/api/image')
def image_tool(file: UploadFile=File(...),format: str=Form('webp'),quality: int=Form(80),width: str=Form(''),height: str=Form('')):
    if format not in ('jpeg','png','webp') or not 1<=quality<=95: raise ValueError('Choose JPEG, PNG or WebP and quality 1–95.')
    with job() as (directory,root):
        try:
            image=ImageOps.exif_transpose(Image.open(file.file)); image.load()
            w=int(width) if width else None; h=int(height) if height else None
            if w is not None and not 1<=w<=10000 or h is not None and not 1<=h<=10000: raise ValueError('Dimensions must be 1–10,000 pixels.')
            if w or h:
                w=w or max(1,round(image.width*h/image.height)); h=h or max(1,round(image.height*w/image.width))
                if w*h>25_000_000: raise ValueError('Maximum output size is 25 megapixels.')
                image=image.resize((w,h),Image.Resampling.LANCZOS)
            if format=='jpeg':
                rgba=image.convert('RGBA'); image=Image.new('RGB',rgba.size,'white'); image.paste(rgba,mask=rgba.getchannel('A'))
            output=root/f'image.{"jpg" if format=="jpeg" else format}'
            image.save(output,format=format.upper(),quality=quality,optimize=True)
            return result_file(directory,output,f'image/{format}')
        except (UnidentifiedImageError,OSError,Image.DecompressionBombError) as exc: raise ValueError('Invalid or oversized image.') from exc

@app.post('/api/qr')
def qr_tool(text: str=Form(...),foreground: str=Form('#123b35'),background: str=Form('#ffffff'),size: int=Form(512)):
    if not text.strip() or len(text.encode())>2000: raise ValueError('Enter between 1 and 2,000 bytes of text.')
    if not 128<=size<=2048 or any(not re.fullmatch('#[0-9a-fA-F]{6}',c) for c in [foreground,background]): raise ValueError('Choose valid hex colours and size 128–2048.')
    with job() as (directory,root):
        qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,border=4); qr.add_data(text); qr.make(fit=True)
        image=qr.make_image(fill_color=foreground,back_color=background).convert('RGB').resize((size,size),Image.Resampling.NEAREST)
        output=root/'qr-code.png'; image.save(output)
        return result_file(directory,output,'image/png')

@app.post('/api/screenshot')
def screenshot_tool(url: str=Form(...),width: int=Form(1440)):
    public_target(url)
    if not 320<=width<=1920: raise ValueError('Width must be 320–1920 pixels.')
    with job() as (directory,root):
        output=root/'screenshot.png'
        try:
            subprocess.run([os.sys.executable,str(Path(__file__).with_name('screenshot_worker.py')),url,str(width),str(output)],check=True,timeout=70,capture_output=True)
        except (subprocess.SubprocessError,OSError) as exc: raise ValueError('Screenshot failed: the site may be unavailable, blocked or too slow.') from exc
        return result_file(directory,output,'image/png')

@app.post('/api/youtube')
def youtube_tool(url: str=Form(...),format: str=Form('mp4')):
    u=urlsplit(url)
    if u.scheme not in ('http','https') or u.hostname not in ('youtube.com','www.youtube.com','m.youtube.com','youtu.be','music.youtube.com') or u.username or u.password or u.port not in (None,80,443): raise ValueError('Enter a YouTube video URL.')
    if format not in ('mp3','mp4'): raise ValueError('Choose MP3 or MP4.')
    with job() as (directory,root):
        cmd=[os.sys.executable,'-m','yt_dlp','--no-config','--no-playlist','--no-warnings','--socket-timeout','20','--retries','1','--max-filesize','150M','--match-filter','duration <= 900 & !is_live','--restrict-filenames','--output',str(root/'%(title).100s.%(ext)s'),'--js-runtimes',f'node:{shutil.which("node") or "/usr/bin/node"}']
        if format=='mp3': cmd+=['-x','--audio-format','mp3','--audio-quality','192K']
        else: cmd+=['-f','bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[ext=mp4]','--merge-output-format','mp4']
        cmd+=['--',url]
        try:
            proc=subprocess.run(cmd,capture_output=True,text=True,timeout=240)
            outputs=list(root.glob(f'*.{format}'))
            if proc.returncode or not outputs:
                error=proc.stderr.lower()
                if 'sign in' in error or 'bot' in error: raise ValueError('YouTube requires verification for this video from this server. Try another video; no cookies are stored.')
                raise ValueError('Download unavailable. Video may be restricted, over 15 minutes, over 150 MB or blocked by YouTube.')
            if outputs[0].stat().st_size>150*1024*1024: raise ValueError('Result exceeds 150 MB.')
            return result_file(directory,outputs[0])
        except subprocess.TimeoutExpired as exc: raise ValueError('Download timed out after four minutes.') from exc

@app.get('/')
def index(): return FileResponse(Path(__file__).parent/'static/index.html')
app.mount('/static',StaticFiles(directory=Path(__file__).parent/'static',check_dir=False),name='static')
