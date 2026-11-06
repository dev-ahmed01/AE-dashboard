"""Render the trusted, bundled property design with database-backed content."""
from pathlib import Path
from bs4 import BeautifulSoup
from html import escape
import json
from urllib.parse import quote

def render_property(p, payload, public_site_url, preview=False):
    html=Path(__file__).with_name("property_template.html").read_text(encoding="utf-8")
    soup=BeautifulSoup(html,"html.parser")
    for link in soup.find_all("link",href=True):
        if link["href"] in ("site.css","rail-refinement.css"):
            link["href"]="/accom-template/"+link["href"]
    for script in soup.find_all("script",src=True):
        if script["src"]=="app.js":
            script["src"]="/accom-template/app.js"
    for img in soup.find_all("img",src=True):
        if img["src"].startswith("assets/"):
            img["src"]="/accom-template/"+img["src"]
    if soup.head:
        for name,content in (("description",p.meta_description or p.description[:160]),
            ("robots","noindex,nofollow" if preview or p.noindex else "index,follow")):
            old=soup.head.find("meta",attrs={"name":name})
            if old:old["content"]=content
            else:soup.head.append(soup.new_tag("meta",attrs={"name":name,"content":content}))
        title=soup.head.find("title")
        if title:title.string=p.seo_title or p.name+" | Accom by Emlen"
        soup.head.append(soup.new_tag("link",attrs={"rel":"canonical",
            "href":public_site_url+"/property/"+quote(p.slug)}))
        schema={"@context":"https://schema.org","@type":"ApartmentComplex",
            "name":p.name,"address":{"@type":"PostalAddress",
                "streetAddress":p.address,"addressLocality":p.city,"addressCountry":p.country}}
        ld=soup.new_tag("script",type="application/ld+json")
        ld.string=json.dumps(schema,ensure_ascii=False).replace("<","\\u003c")
        soup.head.append(ld)
        model=dict(payload)
        model["preview"]=bool(preview)
        model["is_demo"]=bool(p.is_demo)
        data=soup.new_tag("script",id="accom-property-data",type="application/json")
        data.string=json.dumps(model,ensure_ascii=False,default=str).replace("<","\\u003c")
        soup.head.append(data)
        soup.head.append(soup.new_tag("link",attrs={"rel":"stylesheet",
            "href":"/accom-template/integration.css"}))
        soup.head.append(soup.new_tag("script",type="module",src="/accom-template/bridge.js"))
    if p.is_demo and soup.body:
        banner=soup.new_tag("div",attrs={"class":"accom-demo-banner","role":"status"})
        banner.string=("DEMONSTRATION ONLY · Illustrative photos, room rates and dates. "
            "No verified live availability or booking.")
        soup.body.insert(0,banner)
    return str(soup).replace('content="index,follow" name="robots"',
        'name="robots" content="index,follow"').replace(
        'content="noindex,nofollow" name="robots"',
        'name="robots" content="noindex,nofollow"')
