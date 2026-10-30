'use strict';
(() => {
  const icons = {
    youtube: '<rect x="3" y="5" width="18" height="14" rx="4"/><path d="m10 9 5 3-5 3z"/>',
    pdf: '<path d="M14 3H6a1 1 0 0 0-1 1v16h14V8zM14 3v5h5M8 12h8M8 16h5"/>',
    image: '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1.5"/><path d="m3 17 5-5 4 4 4-6 5 7"/>',
    qr: '<path d="M3 3h6v6H3zM15 3h6v6h-6zM3 15h6v6H3zM15 15h3v3h3v3h-6zM12 3v4M3 12h7M12 11v6M18 12h3"/>',
    screenshot: '<rect x="3" y="4" width="18" height="14" rx="2"/><path d="M3 8h18M8 21h8M12 18v3"/>',
    text: '<path d="m8 7-5 5 5 5M16 7l5 5-5 5M14 4l-4 16"/>',
    download: '<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>'
  };
  const svg = name => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name]}</svg>`;
  const field = (label, input, hint = '') => `<div class="field"><label for="${input.match(/id="([^"]+)/)[1]}">${label}</label>${input}${hint ? `<p class="hint">${hint}</p>` : ''}</div>`;
  const url = (placeholder) => field('Paste a link', `<input type="url" id="url" name="url" required placeholder="${placeholder}" inputmode="url" autocomplete="url">`, 'Use a complete URL beginning with https:// or http://.');
  const select = (id, options) => `<select id="${id}" name="${id}">${options.map(([value,label]) => `<option value="${value}">${label}</option>`).join('')}</select>`;
  const tools = {
    youtube: { title: 'YouTube Downloader', description: 'Save a video or just the audio. Keep the good stuff close.', action: 'Prepare download', note: 'Only download content you own or have permission to use. Media is limited to 15 minutes / 150 MB. Some videos may be unavailable due to platform restrictions.', empty: 'Your download will land here', help: 'Add a YouTube link, choose a format, and we’ll take it from there.', form: () => `${url('https://www.youtube.com/watch?v=…')}<fieldset class="field"><legend>Download format</legend><div class="options"><label class="option"><input type="radio" name="format" value="mp4" checked><span><strong>Video <span class="hint">MP4</span></strong><small>Picture and sound</small></span></label><label class="option"><input type="radio" name="format" value="mp3"><span><strong>Audio <span class="hint">MP3</span></strong><small>Just the listening part</small></span></label></div></fieldset>` },
    pdf: { title: 'PDF Tools', description: 'Bring pages together. Pull them apart. Lighten the load.', action: 'Process PDF', note: 'Maximum total upload: 100 MB. Compression may not reduce every PDF, especially files that are already optimized.', empty: 'A fresh PDF, coming up', help: 'Choose an operation and add your PDFs to get started.', form: () => `${field('What would you like to do?', select('operation', [['merge','Merge PDFs'],['split','Split a PDF'],['compress','Compress a PDF']]))}${field('PDF files', '<input type="file" id="files" name="files" accept=".pdf,application/pdf" multiple required>', '<span id="pdf-file-hint">Select two or more PDFs. Files are merged in selection order.</span> Maximum total: 100 MB.')}<div id="pages-field" hidden>${field('Pages to extract (optional)', '<input type="text" id="pages" name="pages" placeholder="1-3,5" disabled>', 'Enter pages such as 1-3,5. Leave blank to split every page into an individual PDF in a ZIP.')}</div>` },
    image: { title: 'Image Tools', description: 'A new format. A better fit. Give your images a little room.', action: 'Convert image', note: 'Maximum total upload: 100 MB. Leave both dimensions blank to keep the original size; set just one to preserve the aspect ratio.', empty: 'Meet your next image', help: 'Upload an image and choose how you’d like it to look.', form: () => `${field('Your image', '<input type="file" id="file" name="file" accept="image/*" required>', 'Choose an image file. Maximum upload: 100 MB.')}<div class="row">${field('Output format', select('format', [['webp','WebP'],['jpeg','JPEG'],['png','PNG']]))}${field('Quality', '<input type="number" id="quality" name="quality" value="85" min="1" max="95" required>', '1–95. Applies to WebP and JPEG.')}</div><div class="row">${field('Width (px, optional)', '<input type="number" id="width" name="width" min="1" placeholder="Original">')}${field('Height (px, optional)', '<input type="number" id="height" name="height" min="1" placeholder="Original">')}</div>` },
    qr: { title: 'QR Generator', description: 'From a small square to somewhere new. Make a code of your own.', action: 'Generate QR code', note: 'Use high-contrast foreground and background colors for reliable scanning. Always test your code before printing or sharing.', empty: 'A small code. Possibilities.', help: 'Add a link or some text and your QR code will appear here.', form: () => `${field('Link or text', '<textarea id="text" name="text" required placeholder="https://your-next-good-idea.com"></textarea>')}<div class="row">${field('Foreground color', '<input type="color" id="foreground" name="foreground" value="#173e34">')}${field('Background color', '<input type="color" id="background" name="background" value="#ffffff">')}</div>${field('Image size (px)', '<input type="number" id="size" name="size" min="128" max="2048" value="512" required>', 'Choose a size between 128 and 2048 pixels.')}` },
    screenshot: { title: 'Web Screenshot', description: 'Keep a little piece of the web. Capture a page as a PNG.', action: 'Capture page', note: 'Only capture pages you have permission to use. Some sites may block automated access or require sign-in; private or protected pages may be unavailable.', empty: 'The web, in a still frame', help: 'Add a public page URL and we’ll prepare a PNG capture.', form: () => `${url('https://example.com')}${field('Browser width (px)', '<input type="number" id="width" name="width" min="320" max="1920" value="1440" required>', 'Choose a viewport width between 320 and 1920 pixels.')}` },
    text: { title: 'Hash & Encode', description: 'The right string, in the right form. No extra steps.', action: 'Transform text', note: 'Hashes are one-way and cannot be decoded. Base64 and URL encoding are reversible, not encryption. Don’t submit passwords or other sensitive information.', empty: 'Your words, transformed', help: 'Choose an operation and enter text to see the result.', form: () => `${field('Operation', select('operation', [['sha256','SHA-256 hash'],['sha512','SHA-512 hash'],['md5','MD5 hash'],['base64_encode','Base64 encode'],['base64_decode','Base64 decode'],['url_encode','URL encode'],['url_decode','URL decode']]))}${field('Your text', '<textarea id="text" name="text" rows="6" required placeholder="Type or paste your text here…" spellcheck="false"></textarea>')}` }
  };
  const form = document.getElementById('tool-form');
  const result = document.getElementById('result');
  let current = '', controller = null, objectURL = null;
  const clearURL = () => { if (objectURL) { URL.revokeObjectURL(objectURL); objectURL = null; } };
  function empty() {
    result.innerHTML = `<div class="empty-icon">${svg(current === 'text' ? 'text' : 'download')}</div><h3>${tools[current].empty}</h3><p>${tools[current].help}</p><span class="empty-label">A LITTLE EVERYDAY MAGIC</span>`;
  }
  function render(key) {
    if (!tools[key]) key = 'youtube';
    if (key === current) return;
    if (controller) controller.abort();
    controller = null;
    clearURL(); current = key;
    form.removeAttribute('aria-busy');
    const tool = tools[key];
    document.querySelectorAll('.nav-item').forEach(button => {
      if (button.dataset.tool === key) button.setAttribute('aria-current', 'page');
      else button.removeAttribute('aria-current');
    });
    document.getElementById('tool-title').textContent = tool.title;
    document.getElementById('tool-number').textContent = String(Object.keys(tools).indexOf(key) + 1).padStart(2, '0');
    document.getElementById('tool-description').textContent = tool.description;
    document.getElementById('tool-note').textContent = tool.note;
    document.getElementById('heading-icon').innerHTML = svg(key);
    document.title = `${tool.title} · Text Box`;
    form.innerHTML = `${tool.form()}<button class="submit" type="submit">${svg(key)}<span>${tool.action}</span><span aria-hidden="true">↗</span></button><div class="form-bottom"><span aria-hidden="true">✧</span> A useful little thing, without the fuss.</div>`;
    empty();
    if (key === 'pdf') form.elements.operation.addEventListener('change', updatePDF);
    if (key === 'image') {
      const quality = form.elements.quality;
      const update = () => {
        const png = form.elements.format.value === 'png';
        quality.closest('.field').hidden = png;
        quality.disabled = png;
      };
      form.elements.format.addEventListener('change', update); update();
    }
  }
  function updatePDF() {
    const operation = form.elements.operation.value;
    const files = form.elements.files;
    files.multiple = operation === 'merge'; files.value = '';
    document.getElementById('pages-field').hidden = operation !== 'split';
    form.elements.pages.disabled = operation !== 'split';
    document.getElementById('pdf-file-hint').textContent = operation === 'merge' ? 'Select two or more PDFs. Files are merged in selection order.' : 'Select one PDF.';
  }
  document.getElementById('tool-nav').innerHTML = Object.entries(tools).map(([key, tool]) => `<button type="button" class="nav-item" data-tool="${key}">${svg(key)}<span>${tool.title}</span></button>`).join('');
  document.getElementById('tool-nav').addEventListener('click', event => {
    const button = event.target.closest('[data-tool]');
    if (button) { location.hash = button.dataset.tool; render(button.dataset.tool); }
  });
  window.addEventListener('hashchange', () => render(location.hash.slice(1)));
  window.addEventListener('pagehide', clearURL);
  function error(message) {
    result.replaceChildren();
    const heading = document.createElement('h3'); heading.textContent = 'That didn’t quite work';
    const text = document.createElement('p'); text.className = 'error-text'; text.textContent = message;
    result.append(heading, text);
  }
  function validate() {
    form.querySelectorAll('input').forEach(input => input.setCustomValidity(''));
    const inputURL = form.querySelector('input[type=url]');
    if (inputURL && inputURL.value) {
      try { if (!['http:', 'https:'].includes(new URL(inputURL.value).protocol)) inputURL.setCustomValidity('Use an http:// or https:// URL.'); }
      catch { inputURL.setCustomValidity('Enter a complete web URL.'); }
    }
    const upload = form.querySelector('input[type=file]');
    if (upload) {
      const files = Array.from(upload.files);
      if (files.reduce((sum, file) => sum + file.size, 0) > 100 * 1024 * 1024) upload.setCustomValidity('The total upload must be 100 MB or less.');
      else if (current === 'pdf' && form.elements.operation.value === 'merge' && files.length < 2) upload.setCustomValidity('Choose at least two PDFs to merge.');
    }
    const pages = form.elements.pages;
    if (pages && !pages.disabled && pages.value.trim() && !/^\d+(?:\s*-\s*\d+)?(?:\s*,\s*\d+(?:\s*-\s*\d+)?)*$/.test(pages.value.trim())) pages.setCustomValidity('Use page numbers and ranges, for example 1-3,5.');
    return form.reportValidity();
  }
  function filename(response, fallback) {
    const header = response.headers.get('Content-Disposition') || '';
    const encoded = header.match(/filename\*\s*=\s*UTF-8''([^;]+)/i);
    let name;
    if (encoded) { try { name = decodeURIComponent(encoded[1].trim()); } catch { /* Try regular filename. */ } }
    if (!name) { const match = header.match(/filename\s*=\s*(?:"([^"]*)"|([^;]+))/i); name = match && (match[1] || match[2]); }
    return (name || fallback).trim().replace(/[\\/\x00-\x1f]/g, '_');
  }
  async function copyResult(textarea, button) {
    try {
      if (!navigator.clipboard || !window.isSecureContext) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(textarea.value);
      button.textContent = 'Copied!';
    } catch {
      textarea.focus(); textarea.select(); textarea.setSelectionRange(0, textarea.value.length);
      let copied = false;
      try { copied = document.execCommand('copy'); } catch { /* Selection remains for manual copy. */ }
      button.textContent = copied ? 'Copied!' : 'Selected — press Ctrl/Cmd + C';
    }
  }
  ['input', 'change'].forEach(type => form.addEventListener(type, event => {
    if (typeof event.target.setCustomValidity === 'function') event.target.setCustomValidity('');
  }));
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!validate() || controller) return;
    clearURL();
    const key = current;
    const data = new FormData(form);
    // PNG has no lossy quality control, but the API still accepts a quality field.
    if (key === 'image' && !data.has('quality')) data.set('quality', '85');
    const request = new AbortController(); controller = request;
    const submit = form.querySelector('[type=submit]'); submit.disabled = true;
    form.setAttribute('aria-busy', 'true');
    result.innerHTML = '<div class="spinner" aria-hidden="true"></div><h3>Working a little magic…</h3><p>Please keep this tab open. Larger files and web captures can take a moment.</p>';
    try {
      const response = await fetch(`/api/${key}`, { method: 'POST', body: data, signal: request.signal });
      if (!response.ok) {
        let message = `The request failed (${response.status}). Please try again.`;
        const type = response.headers.get('content-type') || '';
        if (type.includes('json')) {
          const body = await response.json();
          const detail = body.error || body.detail || body.message;
          if (typeof detail === 'string') message = detail;
          else if (Array.isArray(detail)) message = detail.map(item => item.msg || 'Invalid input').join('; ');
        } else { const text = await response.text(); if (text && !text.trim().startsWith('<')) message = text.slice(0, 400); }
        throw new Error(message);
      }
      if (key === 'text') {
        const body = await response.json();
        if (typeof body.result !== 'string') throw new Error('The server returned an unexpected text result.');
        if (request.signal.aborted || current !== key) return;
        result.innerHTML = '<h3>Transformation complete</h3><label class="hint" for="text-result">Your result</label><textarea id="text-result" readonly spellcheck="false"></textarea><button type="button" class="secondary">Copy result</button>';
        const textarea = result.querySelector('textarea'); textarea.value = body.result;
        const button = result.querySelector('button'); button.addEventListener('click', () => copyResult(textarea, button));
      } else {
        const blob = await response.blob();
        if (request.signal.aborted || current !== key) return;
        if (!blob.size) throw new Error('The server returned an empty file. Please try again.');
        objectURL = URL.createObjectURL(blob);
        result.replaceChildren();
        if (['image', 'qr', 'screenshot'].includes(key)) {
          const preview = document.createElement('img'); preview.src = objectURL; preview.alt = `${tools[key].title} output preview`;
          result.append(preview);
        }
        const title = document.createElement('h3'); title.textContent = 'All yours. Ready to download.';
        const name = filename(response, key === 'youtube' ? `muggle-download.${data.get('format')}` : key === 'pdf' ? (data.get('operation') === 'split' && !String(data.get('pages') || '').trim() ? 'muggle-pages.zip' : 'muggle-document.pdf') : key === 'image' ? `muggle-image.${data.get('format')}` : `muggle-${key}.png`);
        const info = document.createElement('p'); info.className = 'file-name'; info.textContent = name;
        const link = document.createElement('a'); link.className = 'download'; link.href = objectURL; link.download = name; link.textContent = 'Download file ↓';
        result.append(title, info, link);
      }
    } catch (failure) {
      if (!request.signal.aborted && current === key) error(failure instanceof TypeError ? 'Could not reach the service. Check your connection and try again.' : failure.message || 'Something went wrong. Please try again.');
    } finally {
      if (controller === request) { controller = null; submit.disabled = false; form.removeAttribute('aria-busy'); }
    }
  });
  render(location.hash.slice(1));
  const health = document.getElementById('health');
  const timeout = new AbortController();
  const timer = setTimeout(() => timeout.abort(), 8000);
  fetch('/api/health', { signal: timeout.signal }).then(async response => {
    if (!response.ok) throw new Error('Unavailable');
    await response.json();
    health.classList.add('online'); health.querySelector('span').textContent = 'Service online';
  }).catch(() => { health.classList.add('offline'); health.querySelector('span').textContent = 'Service unreachable'; }).finally(() => clearTimeout(timer));
})();
