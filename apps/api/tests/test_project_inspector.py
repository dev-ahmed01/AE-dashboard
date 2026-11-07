from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import pytest

from project_inspector import inspect_project, extract_html_from_zip

def zip_bytes(files):
    b=BytesIO()
    with ZipFile(b,'w',ZIP_DEFLATED) as z:
        for name,content in files.items():
            z.writestr(name,content)
    return b.getvalue()

def test_next_project_routes_and_editable_candidates():
    src=zip_bytes({
      'package.json':'{"dependencies":{"next":"15.0.0"},"scripts":{"build":"next build"}}',
      'src/app/page.tsx':'export default function Home(){return <main><h1>Find your student room</h1><button>Get help</button><img src="/hero.webp"/></main>}',
      'src/app/locations/[city]/page.tsx':'export default function City(){return <section><h1>Student homes in Bristol</h1><a href="/contact">Explore rooms</a></section>}',
      'src/app/layout.tsx':'export default function Layout(){}',
    })
    result=inspect_project('accom-project.zip',src)
    assert result['framework']=='Next.js'
    assert {p['route'] for p in result['pages']}=={'/','/locations/[city]'}
    assert result['renderable_pages']==0
    home=next(p for p in result['pages'] if p['route']=='/')
    assert 'Find your student room' in home['headings']
    assert 'Get help' in home['cta_labels']
    assert '/hero.webp' in home['image_references']

def test_static_export_is_recognized_and_extractable():
    source='<html><body><main><h1>Student accommodation</h1><section><h2>Nearby universities</h2><p>Find the right home.</p></section></main></body></html>'
    data=zip_bytes({'dist/index.html':source,'dist/assets/style.css':'h1{color:red}'})
    result=inspect_project('published-site.zip',data)
    assert result['renderable_pages']==1
    assert extract_html_from_zip(data,'dist/index.html')==source
    with pytest.raises(ValueError,match='not found'):
        extract_html_from_zip(data,'other/index.html')

def test_js_only_shell_requires_build():
    data=zip_bytes({'dist/index.html':'<html><body><div id="root"></div><script src="/assets/main.js"></script></body></html>'})
    result=inspect_project('app.zip',data)
    assert result['renderable_pages']==0
    with pytest.raises(ValueError,match='Build or statically export'):
        extract_html_from_zip(data,'dist/index.html')

def test_reject_zip_path_traversal():
    malicious=zip_bytes({'../outside.jsx':'export default ()=><h1>No</h1>'})
    with pytest.raises(ValueError,match='unsafe'):
        inspect_project('project.zip',malicious)

def test_reject_excessive_files():
    files={f'src/pages/a{i}.jsx':'export default ()=><h1>Hello</h1>' for i in range(501)}
    with pytest.raises(ValueError,match='too many files'):
        inspect_project('big.zip',zip_bytes(files))

def test_single_vue_source_is_inspectable_without_execution():
    result=inspect_project('Listing.vue',b'<template><section><h1>All apartments</h1><a>Enquire</a></section></template>')
    assert result['pages'][0]['headings']==['All apartments']
    assert result['pages'][0]['requires_build']
