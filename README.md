# Muggle Toolbox

A self-hosted utility workbench for a trusted LAN/WireGuard network. FastAPI backend, vanilla HTML/CSS/JavaScript frontend, no external UI assets or analytics.

## Tools

- **YouTube Downloader:** yt-dlp + its packaged EJS solver, Node and FFmpeg. MP4 video (up to 1080p) or MP3 audio. Single videos, at most 15 minutes and 150 MiB. YouTube may restrict individual videos; only download content you have rights to use.
- **PDF:** merge in upload order, extract a page range (`1-3,5`), split all pages into a ZIP, lossless stream compression and duplicate removal. Compression returns the original if the rewrite would increase size. No image downsampling; already-compressed PDFs may not shrink.
- **Images:** JPEG/PNG/WebP conversion, quality controls for JPEG/WebP, resize; one dimension preserves aspect ratio. EXIF orientation applied; metadata not copied. Transparency flattened onto white for JPEG. Animated files use the first frame. Maximum 25 megapixels.
- **QR:** custom foreground/background, 128–2048px PNG. Use contrasting colours and verify with a scanner before printing.
- **Screenshot:** Playwright Chromium full-page PNG, viewport 320–1920px; maximum page height 20,000px. A public-IP-only HTTP CONNECT proxy validates and pins resolved addresses on each connection, including assets and redirects. Private/reserved destinations and non-standard ports are blocked. Browser profiles are disposable. Authenticated pages are not supported.
- **Text:** MD5, SHA-256, SHA-512, UTF-8 Base64 encode/decode, URL encode/decode. MD5 is for legacy checksums, not secure password storage.

## Private deployment

Configured address: **http://192.168.31.150:5082**. Available directly on the LAN and through the existing WireGuard LAN route, like Hermes WebUI. No public tunnel or router forwarding is configured. No separate login: anyone with network access to this port can use it; do not expose it to the internet. HTTP is encrypted in transit only when carried inside WireGuard.

- Source: `/root/workspace/muggle-toolbox`
- Runtime copy: `/opt/muggle-toolbox`
- Service: `muggle-toolbox.service` (enabled at boot; no dependency on VPN startup)
- Dedicated service user: `muggle-toolbox`
- Read-only filesystem and home protection, private temporary directory, no capabilities, 2GiB memory / two CPU quota, two simultaneous processing tasks.
- Files are temporary and removed after response delivery or processing failure. Browser downloads stay on the user's device. Abrupt crashes can leave temporary files until the service's private temporary directory is removed. Input uploads are capped at 100 MiB total, including multipart overhead.
- Host and cross-origin request checks protect the browser-facing API. Do not treat this as authentication.

## Development

Prerequisites: Python 3.11+, uv, FFmpeg, Node, Chromium system libraries.

```sh
uv sync --frozen
uv run playwright install --with-deps chromium
uv run pytest -q
uv run uvicorn app:app --host 192.168.31.150 --port 5082 --no-proxy-headers
```

The supplied configuration deliberately permits only the configured host/IP and port. If deploying elsewhere, update `ALLOWED_HOSTS` in `app.py`, the bind address in the service unit, and the live-smoke base URL. Do not run the development server on the production port at the same time as the service.

Deployment template: `deploy/muggle-toolbox.service`. Install the project into `/opt/muggle-toolbox`, build a fresh venv there with `uv sync --frozen`, put Node on the service PATH and install browsers using `PLAYWRIGHT_BROWSERS_PATH=/opt/muggle-toolbox/browsers`. Give the dedicated service group read/traverse access, not write access, to application files. The service's `ProtectHome=true` intentionally prevents dependencies under `/root` being used. Install the unit in `/etc/systemd/system/` and enable it. Do not copy a venv from a different absolute path.

For updates, run tests in the source tree, copy changed application/static files into the runtime tree with the service group ownership/read permissions, synchronize locked dependencies if needed, then restart and health-check the service. Do not replace the runtime's browser directory, Node binary or venv accidentally.

```sh
systemctl restart muggle-toolbox
curl --noproxy '*' --retry 6 --retry-connrefused http://192.168.31.150:5082/api/health
```

## Verification

`uv run pytest -q` runs isolated API checks. `uv run python tests/live_smoke.py` exercises the deployed service, generates fixture PDFs/images, captures a real website, downloads the public Big Buck Bunny test video in MP4 and MP3, and verifies desktop/mobile UI via Chromium. It requires network access, downloads up to ~165 MB, writes test outputs/screenshots under `/tmp`, and may fail if third-party sites change. Unit tests do not rely on YouTube availability.

All six tools were exercised against the deployed service. MP4 video/audio streams and MP3 audio were confirmed with ffprobe. Browser navigation, hash output and QR preview passed at desktop/mobile widths without JavaScript errors. Host-side LAN connectivity was verified; an outside-network VPN-client test remains an operator-side check.
