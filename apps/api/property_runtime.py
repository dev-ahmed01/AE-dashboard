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

    # Render the property identity and all visible facts on the server too.
    # Search crawlers and users without JS must never see Kingston sample
    # facts on a different residence.
    def fill(selector,text):
        el=soup.select_one(selector)
        if el:el.clear();el.append(str(text or ''))
    fill('#property-title',p.name)
    fill('.address',', '.join(x for x in [p.address,p.postcode,p.city] if x))
    fill('.cta-property-title h2',p.name)
    fill('.cta-address',', '.join(x for x in [p.address,p.postcode,p.city] if x))
    fill('.cta-kicker','STUDENT LIVING · '+(p.city or 'UK').upper())
    # Keep the design, but never leak the prototype's property-specific copy.
    fill('#overview .overview-priority-intro p:last-of-type',p.description)
    fill('.access-section p','Tell us your accessibility requirements. Ask the accommodation provider to confirm step-free access, lift dimensions and room specifications before booking.')
    verified_mark=soup.select_one('.verified-mark')
    if verified_mark:
        verified_mark['title']='Accommodation details require provider confirmation'
        verified_mark['aria-label']='Check current property details with the provider'
    cta_verified=soup.select_one('.cta-verified')
    if cta_verified:cta_verified['title']='Confirm details with accommodation provider'
    if not p.is_demo:
        # No provider-sourced house rules are stored yet; do not display
        # unverified prototype rules or Kingston-specific related content.
        for selector in ('#house-rules','.section-nav a[href="#house-rules"]','.related-section'):
            el=soup.select_one(selector)
            if el:el.decompose()
    fill('.verified-copy','Demo sample' if p.is_demo else 'Details to confirm')
    fill('.overview-footnote','Illustrative room rates and photography; verify availability.' if p.is_demo
         else 'Confirm room specifications and current contract details before booking.')
    fill('.cta-footnote','Illustrative sample, no live booking.' if p.is_demo
         else 'All prices and availability require confirmation with the operator.')
    fill('.site-footer .footer-meta','Property detail demo only' if p.is_demo
         else 'Accommodation enquiries only. No rent collected.')
    fill('#enquiry-dialog .enquiry-visual p','Ask us to confirm room availability and contract terms. This is an enquiry, not a booking.')
    fill('.cta-price-hero small','Illustrative from' if p.is_demo else 'Rooms from')
    price=payload.get('from_price')
    currency=payload.get('currency') or 'GBP'
    period=payload.get('price_period') or 'week'
    symbol={'GBP':'£','EUR':'€','USD':'$'}.get(currency,currency+' ')
    amount=('Price on request' if price is None else symbol+f'{float(price):,.0f}')
    fill('#cta-from-price',amount)
    fill('#mobile-price','Price on request' if price is None else
         'From '+amount+('/mo' if period=='month' else '/wk'))
    period_badge=soup.select_one('.cta-price-hero .cta-overview-value span')
    if period_badge:period_badge.string=('/ '+period if price is not None else '')
    for i,node in enumerate(soup.select('.overview-highlight')):
        if i>=len(p.highlights or []):
            node.decompose()
        else:
            label=node.select_one('strong')
            detail=node.select_one('small')
            if label:label.string=p.highlights[i]
            if detail:detail.string='Check current details'
    landmarks=soup.select_one('.landmarks-grid')
    if landmarks:
        landmarks.clear()
        for item in (p.landmarks or []):
            card=soup.new_tag('div',attrs={'class':'landmark-card','role':'listitem'})
            heading=soup.new_tag('strong')
            heading.string=item.get('name','')
            sub=soup.new_tag('small')
            sub.string=item.get('detail','')
            card.append(heading);card.append(sub);landmarks.append(card)
    fill('.landmarks-footnote','Distances and nearby facilities should be verified using current maps and operator information.')
    included=soup.select_one('.included-list')
    if included:
        included.clear()
        for amenity in (p.amenities or []):
            li=soup.new_tag('li')
            label=soup.new_tag('span');label.string=amenity
            small=soup.new_tag('small');small.string='Verify with operator'
            li.append(label);li.append(small);included.append(li)
    fill('.inclusion-secondary','Ask Accom about optional charges, utilities and the current contract.')
    if not p.review_source_url:
        review=soup.select_one('.cta-rating')
        if review:review.decompose()
    else:
        fill('.cta-rating strong',payload.get('review_score') or 'Reviews')
        fill('.cta-rating small',str(payload.get('review_count') or '')+' attributed reviews')
    for i,item in enumerate(soup.select('.cta-benefit')):
        highlights=p.highlights or []
        if i>=len(highlights):item.decompose();continue
        heading=item.select_one('strong')
        caption=item.select_one('.cta-benefit-copy span')
        if heading:heading.string=highlights[i]
        if caption:caption.string='Confirm details'
    if soup.select_one('.cta-google-map'):
        query=', '.join(x for x in [p.address,p.city,p.postcode] if x)
        from urllib.parse import quote as urlquote
        map_node=soup.select_one('.cta-google-map')
        map_node['src']='https://maps.google.com/maps?q='+urlquote(query)+'&z=16&output=embed'
        map_node['title']='Map showing '+p.name
        map_card=soup.select_one('.cta-google-map-card')
        if map_card:map_card['aria-label']='Map of '+p.name
        directions=soup.select_one('.cta-google-map-caption a')
        if directions:
            directions['href']='https://www.google.com/maps/search/?api=1&query='+urlquote(query)
            directions['aria-label']='Open '+p.name+' location in Google Maps'
    fill('.cta-google-map-place strong',p.name)
    fill('.cta-google-map-place small',p.address)
    gallery=soup.select_one('.gallery-grid')
    images=p.gallery or []
    if gallery:
        existing=list(gallery.select('.gallery-tile'))
        for i,item in enumerate(images):
            if i<len(existing):
                el=existing[i]
            else:
                # Every uploaded image appears in the mosaic AND lightbox.
                el=soup.new_tag('button',attrs={'class':'gallery-tile','type':'button'})
                el.append(soup.new_tag('img',attrs={'loading':'lazy','decoding':'async'}))
                gallery.append(el)
            img=el.find('img')
            if img:
                img['src']=item.get('url','')
                img['alt']=item.get('alt','Property photo')
            el['data-gallery-index']=str(i)
            el['aria-label']='Open '+item.get('alt','property photo')+' in gallery'
            el['class']=[c for c in el.get('class',[]) if c!='gallery-main']
            if item.get('layout')=='large':el['class'].append('gallery-main')
        for el in existing[len(images):]:el.decompose()
        if len(images)==1:gallery['class'].append('single-photo')
    fill('#view-gallery','View all '+str(len(p.gallery or []))+' photos')
    image=soup.select_one('#lightbox-image')
    if image:
        image['src']=images[0].get('url','') if images else ''
        image['alt']=images[0].get('alt','Property photo') if images else 'No photographs available'
    if not images:
        all_photos=soup.select_one('#view-gallery')
        if all_photos:all_photos['disabled']=''
    # Replace fixed prototype addresses/text in remaining incidental labels.
    for text_node in soup.find_all(string=True):
        if text_node.parent.name in ('script','style'):continue
        text_value=str(text_node)
        if 'iQ Kingston' in text_value:
            text_node.replace_with(text_value.replace('iQ Kingston',p.name))

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
