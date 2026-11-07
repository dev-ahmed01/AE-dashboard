"""Safe, non-executing discovery of pages in source project archives.

We do not run npm, import project modules or evaluate arbitrary uploaded code.
A discovered React/Vue/etc. route is a mapping candidate, NOT a live HTML page.
"""
from __future__ import annotations

import io
import json
import posixpath
import re
import zipfile
from pathlib import PurePosixPath

MAX_ARCHIVE_BYTES = 24 * 1024 * 1024
MAX_ENTRIES = 500
MAX_UNCOMPRESSED = 45 * 1024 * 1024
MAX_ONE_FILE = 6 * 1024 * 1024
SOURCE_EXTS = {'.html', '.htm', '.jsx', '.tsx', '.vue', '.svelte', '.astro', '.js', '.ts'}
IGNORE_PARTS = {'node_modules', '.git', '.next', '.nuxt', '.svelte-kit', '__pycache__', 'coverage', 'vendor'}
HEAD_RE = re.compile(r'<h([1-6])\b[^>]*>(.*?)</h\1>', re.I | re.S)
LINK_RE = re.compile(r'<(?:a|button)\b[^>]*>(.*?)</(?:a|button)>', re.I | re.S)
IMG_RE = re.compile(r"<img\b[^>]*(?:src|data-src)\s*=\s*['\"]([^'\"]+)", re.I)
HTML_RE = re.compile(r'<(?:html|main|section|article|h1|h2)\b', re.I)
ROUTE_RE = re.compile(r"<Route\b[^>]*path\s*=\s*['\"]([^'\"]+)['\"]", re.I)
TEXT_RE = re.compile(r'<[^>]+>|\{[^{}]*\}')
INVALID_PATH = re.compile(r'(^/|\\|(^|/)\.\.(?:/|$)|[\x00-\x1f])')
TAG_STRIP = re.compile(r'<[^>]*>|\{[^{}]*\}')

def _plain(value: str) -> str:
    return re.sub(r'\s+', ' ', TAG_STRIP.sub('', value)).strip()[:150]

def _route(path: str) -> str | None:
    p = path.replace('\\\\', '/').strip('/')
    parts = p.split('/')
    if any(x in IGNORE_PARTS for x in parts):
        return None
    ext = PurePosixPath(p).suffix.lower()
    if ext not in SOURCE_EXTS:
        return None
    stem = PurePosixPath(p).stem
    if stem.startswith('_') or stem in ('layout', 'loading', 'error', 'not-found', 'middleware'):
        return None
    # Next app router: app/locations/[city]/page.tsx
    if 'app' in parts and stem == 'page':
        i = parts.index('app')
        route_parts = [x for x in parts[i + 1:-1] if not (x.startswith('(') and x.endswith(')'))]
        return '/' + '/'.join(route_parts)
    for anchor in ('pages', 'routes'):
        if anchor in parts:
            i = parts.index(anchor)
            route_parts = parts[i + 1:]
            if route_parts and route_parts[-1].split('.')[0] == 'index':
                route_parts = route_parts[:-1]
            elif route_parts:
                route_parts[-1] = PurePosixPath(route_parts[-1]).stem
            return '/' + '/'.join(route_parts)
    if stem in ('App', 'index', 'main') and ext in {'.tsx', '.jsx', '.html', '.htm'}:
        return '/'
    if ext in ('.html', '.htm') and (p.startswith('dist/') or p.startswith('build/') or p.startswith('out/') or '/' not in p):
        sub = p.split('/', 1)[-1] if '/' in p else p
        name = PurePosixPath(sub).stem
        return '/' if name == 'index' else '/' + name
    return None

def _inspect_text(path: str, source: str) -> dict:
    headings = [_plain(m.group(2)) for m in HEAD_RE.finditer(source)]
    headings = [h for h in headings if h and not h.startswith('$')]
    ctas = [_plain(m.group(1)) for m in LINK_RE.finditer(source)]
    ctas = [x for x in ctas if x][:8]
    images = [x for x in IMG_RE.findall(source) if not x.startswith(('data:', '$', '{'))][:8]
    fields = []
    for m in HEAD_RE.finditer(source):
        value = _plain(m.group(2))
        if value:
            fields.append({'kind':'heading', 'tag':'h'+m.group(1), 'value':value})
    for item in ctas:
        fields.append({'kind':'cta', 'value':item})
    for item in images:
        fields.append({'kind':'image', 'value':item})
    route = _route(path)
    html = PurePosixPath(path).suffix.lower() in ('.html', '.htm')
    meaningful = html and bool(HTML_RE.search(source)) and bool(headings)
    return {
        'file':path, 'route':route or '(component)', 'type':'HTML' if html else PurePosixPath(path).suffix.lstrip('.').upper(),
        'headings':headings[:8], 'cta_labels':ctas, 'image_references':images,
        'fields':fields[:60], 'renderable_html':bool(meaningful),
        'requires_build':not bool(meaningful),
    }

def _safe_entries(raw: bytes):
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError('The ZIP project must be 24 MB or smaller')
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile as error:
        raise ValueError('The uploaded ZIP archive is invalid') from error
    entries = archive.infolist()
    if len(entries) > MAX_ENTRIES:
        raise ValueError('ZIP contains too many files (maximum 500)')
    if sum(entry.file_size for entry in entries) > MAX_UNCOMPRESSED:
        raise ValueError('Expanded ZIP is too large')
    for entry in entries:
        name = entry.filename
        if INVALID_PATH.search(name) or name.startswith('.') or posixpath.normpath(name) != name.strip('/'):
            raise ValueError('ZIP includes an unsafe file path')
        # Reject symlinks and encrypted entries; never write upload entries to disk.
        if entry.flag_bits & 1 or ((entry.external_attr >> 16) & 0o170000) == 0o120000:
            raise ValueError('ZIP contains an unsupported encrypted or symbolic-link entry')
        if entry.file_size > MAX_ONE_FILE:
            continue
        p = PurePosixPath(name)
        if entry.is_dir() or any(part in IGNORE_PARTS for part in p.parts):
            continue
        if p.suffix.lower() not in SOURCE_EXTS and p.name != 'package.json':
            continue
        yield archive, entry

def inspect_project(filename: str, raw: bytes) -> dict:
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError('Project upload is too large (maximum 24 MB)')
    project = (filename or '').lower()
    files = {}
    package = {}
    if project.endswith('.zip'):
        for archive, entry in _safe_entries(raw):
            body = archive.read(entry)
            try:
                text = body.decode('utf-8')
            except UnicodeDecodeError:
                continue
            if entry.filename.endswith('package.json'):
                try: package = json.loads(text)
                except (ValueError, TypeError): pass
            else:
                files[entry.filename] = text
    elif PurePosixPath(project).suffix in SOURCE_EXTS:
        try: files[PurePosixPath(filename).name] = raw.decode('utf-8')
        except UnicodeDecodeError as error: raise ValueError('Use UTF-8 project files') from error
    else:
        raise ValueError('Upload a ZIP project or HTML, JSX, TSX, Vue, Svelte or Astro file')
    pages = [_inspect_text(path, content) for path, content in files.items()]
    # Prefer route/page entrypoints; ignore low-value support modules.
    pages = [p for p in pages if p['route'] != '(component)' or p['headings']]
    pages.sort(key=lambda p:(p['route']=='(component)',p['route'],p['file']))
    pages = pages[:60]
    if not pages:
        raise ValueError('No page or component source was found. Include src/pages, app routes, or a built HTML export.')
    framework = 'Next.js' if any('/app/' in '/' + p or '/pages/' in '/' + p for p in files) and isinstance(package.get('dependencies'),dict) and 'next' in package['dependencies'] else ('React / Vite' if any(p.endswith(('.jsx','.tsx')) for p in files) else 'Static / mixed project')
    return {
        'filename':filename, 'framework':framework, 'pages':pages, 'source_files':len(files),
        'total_fields':sum(len(p['fields']) for p in pages),
        'renderable_pages':sum(1 for p in pages if p['renderable_html']),
        'recommended_build_command':'npm run build' if package.get('scripts',{}).get('build') else 'Export a static build from your framework',
        'message':'Route and content candidates detected. Source components are not rendered or executed. Upload a built static HTML export for visual template importing.',
    }

def extract_html_from_zip(raw: bytes, path: str) -> str:
    for archive, entry in _safe_entries(raw):
        if entry.filename == path:
            if PurePosixPath(path).suffix.lower() not in ('.html','.htm'):
                raise ValueError('Selected file is not HTML. Build the project before importing.')
            try: source = archive.read(entry).decode('utf-8')
            except UnicodeDecodeError as error: raise ValueError('HTML must be UTF-8') from error
            if not _inspect_text(path,source)['renderable_html']:
                raise ValueError('Built HTML has no meaningful markup. Build or statically export the page; a JavaScript shell cannot be mapped.')
            return source
    raise ValueError('Selected HTML file was not found in the project archive')
