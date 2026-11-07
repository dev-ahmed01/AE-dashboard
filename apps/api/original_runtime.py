"""Render every Accom listing using the exact approved 13-section master design.

The master is a copy of the deployed Accom page, with its original CSS and
interactive scripts externalized for CSP compatibility. We replace content in
the original DOM; we do not recreate a lookalike page.
"""
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import quote
import json
import re

MASTER = Path(__file__).with_name("property_master.html")
EMPTY_GIF = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
ALLOWED_IMAGE = re.compile(r"^(https://[^\s<>\"']+|/(?:api/media/[0-9]+|accom-template/assets/[a-zA-Z0-9_-]+\.(?:webp|jpg|jpeg|png)))$")
HERO_SECTIONS = ("overview", "about", "tours", "amenities", "rooms", "rules", "payments", "floorplan",
                 "neighbourhood", "faqs", "location", "reviews")


def _list(value):
    return value if isinstance(value, list) else []


def _text(value):
    return str(value or "").strip()


def _safe_image(value):
    url = _text(value)
    return url if ALLOWED_IMAGE.fullmatch(url) else ""


def _put(soup, selector, text):
    item = soup.select_one(selector)
    if item:
        item.clear()
        item.append(_text(text))
    return item


def _paragraph(soup, text):
    node = soup.new_tag("p")
    node.string = _text(text)
    return node


def _empty(soup, selector, text):
    node = soup.select_one(selector)
    if node:
        node.clear()
        node.append(_paragraph(soup, text))


def _details(soup, selector, items, fallback):
    box = soup.select_one(selector)
    if not box:
        return
    box.clear()
    pairs = [( _text(x.get("question")), _text(x.get("answer"))) for x in _list(items)
             if isinstance(x, dict) and _text(x.get("question"))]
    if not pairs:
        pairs = [(fallback, "Please ask our team to confirm the current property information.")]
    for question, answer in pairs:
        details = soup.new_tag("details")
        summary = soup.new_tag("summary")
        summary.append(question + " ")
        mark = soup.new_tag("span")
        mark.string = "+"
        summary.append(mark)
        details.append(summary)
        details.append(_paragraph(soup, answer or "Ask the accommodation provider to confirm."))
        box.append(details)


def _photos(soup, photos, preview):
    valid = [p for p in _list(photos) if isinstance(p, dict) and _safe_image(p.get("url"))]
    sample = preview and not valid
    gallery = soup.select_one("section.gallery")
    tiles = soup.select("section.gallery > .gallery-tile")
    if gallery is None:
        return valid
    for i, tile in enumerate(tiles):
        img = tile.select_one("img")
        if valid and i < len(valid):
            item = valid[i]
            img["src"] = _safe_image(item.get("url"))
            img["alt"] = _text(item.get("alt")) or "Property photo"
            img.attrs.pop("data-asset", None)
            tile["data-open-image"] = str(i)
            tile["aria-label"] = "Open " + img["alt"]
            tile["class"] = ["gallery-tile"] + (["gallery-large"] if item.get("layout") == "large" or i == 0 else [])
        elif valid or not sample:
            tile.decompose()
    if valid and len(valid) == 1:
        gallery["style"] = "grid-template-columns:1fr;grid-template-rows:1fr;"
    if valid:
        first = valid[0]
        for selector in ("#photoActive", "#neighbourhood .neighbourhood-layout img"):
            node = soup.select_one(selector)
            if node:
                node["src"] = _safe_image(first.get("url"))
                node["alt"] = _text(first.get("alt")) or "Property photo"
                node.attrs.pop("data-asset", None)
    elif not sample:
        placeholder = soup.new_tag("div", attrs={"class": "accom-master-photo-placeholder", "role": "status"})
        placeholder.string = "Property photos coming soon"
        gallery.append(placeholder)
        gallery["style"] = "display:grid;place-items:center;min-height:290px;"
    count = len(valid) if valid else (7 if sample else 0)
    for selector in ('[data-open-gallery].gallery-view', ".gallery-category-menu [data-open-gallery] span",
                     '#photoTabs [data-photo-category="all"] span'):
        node = soup.select_one(selector)
        if node:
            if selector.startswith("[data"):
                span = node.select_one("svg")
                node.clear()
                if span:
                    node.append(span)
                node.append(" View all " + str(count) + " photos")
            else:
                node.string = str(count)
    if not count:
        for el in soup.select("[data-open-gallery], [data-open-image], [data-open-category]"):
            el["disabled"] = ""
    if sample:
        label = soup.new_tag("p", attrs={"class": "accom-master-preview-note", "role": "status"})
        label.string = "Template sample photos · Add your property's approved images before publishing"
        gallery.insert_after(label)
    # Master inline source uses data-asset on all secondary sample thumbnails. They
    # are shown in *preview* for layout fidelity and hidden on real listings without media.
    for el in soup.select("#tours .photo-category-grid button"):
        img = el.select_one("img")
        if not img:
            continue
        if valid:
            idx = list(soup.select("#tours .photo-category-grid button")).index(el)
            item = valid[min(idx, len(valid) - 1)]
            img["src"] = _safe_image(item.get("url"))
            img["alt"] = _text(item.get("alt")) or "Property photo"
            img.attrs.pop("data-asset", None)
        elif not sample:
            el.decompose()
    return valid


def render_property(p, payload, public_site_url, preview=False):
    html = MASTER.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    name = _text(getattr(p, "name", "")) or "Untitled property"
    city = _text(getattr(p, "city", ""))
    address = ", ".join(x for x in (_text(getattr(p, "address", "")),
                                    _text(getattr(p, "postcode", "")), city) if x)
    demo = bool(getattr(p, "is_demo", False))
    desc = _text(getattr(p, "description", "")) or "Contact Accom to confirm the latest property details."
    amenities = [_text(x) for x in _list(getattr(p, "amenities", [])) if _text(x)]
    highlights = [_text(x) for x in _list(getattr(p, "highlights", [])) if _text(x)]
    landmarks = [x for x in _list(getattr(p, "landmarks", [])) if isinstance(x, dict)]
    reviews = [x for x in _list(getattr(p, "reviews", [])) if isinstance(x, dict) and _text(x.get("quote"))]
    rooms = _list(payload.get("rooms"))
    photos = _photos(soup, getattr(p, "gallery", []), preview)

    for selector in (".property-heading h1", ".crumbs strong", ".landmarks-detail > strong",
                     "#galleryDialog .modal-header strong", ".modal-context"):
        _put(soup, selector, name)
    _put(soup, ".crumbs a[href='#location']", city or "Location")
    _put(soup, ".property-address", address or "Address to be confirmed")
    _put(soup, ".rail-title", "Rooms at " + name)
    _put(soup, ".rail-nearby-header span", "Near " + name)
    _put(soup, "#about h2", "Living at " + name)
    _put(soup, "#amenities h2", "What's included at " + name)
    _put(soup, "#overview .intro-text", desc)
    _put(soup, "#about .story-lede", desc)
    for node in soup.select("#about .story-detail"):
        node.string = "Explore the accommodation, room options and available facilities. Confirm details directly with the property team."
    _put(soup, ".story-guide-note", "Room facilities and availability should be confirmed with the property operator.")
    _put(soup, "#neighbourhood .neighbourhood-layout p", "Explore the neighbourhood around " + (city or name) + ". Ask for confirmed local transport and university routes.")
    for node in soup.select("#neighbourhood .neighbourhood-layout p")[1:]:
        node.decompose()
    _put(soup, "#location .section-intro", "Explore nearby places. Distances and transport times should be verified before travelling.")
    _put(soup, "#location .landmarks-detail > p", address or "Location details to be confirmed")
    _put(soup, "#tours .source-caption", "Only approved property photography should be published. Request current photos and virtual tours from the operator.")
    _put(soup, "#rooms .source-caption", "Ask the accommodation provider to confirm rates, availability and full contract totals.")
    _put(soup, "#rooms .section-title-row p", "Compare available rooms and ask for a full tenancy quotation before booking.")
    _put(soup, ".rail-nearby-source", "Check current routes and travel times with maps before visiting.")
    _put(soup, "#amenities .source-caption", "Confirm which services and utilities are covered by your current contract.")
    _put(soup, "#amenities .bill-disclosure", "Personal budgeting illustration only. Confirm included utilities and their terms with the operator.")
    _put(soup, ".room-pricing-summary span", str(len(rooms)) + " room options · confirm price and availability before booking")
    _put(soup, ".rail-attribution", "Current rates and availability require confirmation.")
    _put(soup, ".railRoom", "Ask for room options")
    _put(soup, ".room-pricing-summary strong", "Room prices on request" if payload.get("from_price") is None
         else "From £" + str(int(float(payload.get("from_price")))) + "/" + ("month" if payload.get("price_period") == "month" else "week"))
    _put(soup, ".mobile-cta small", "Prices to confirm")
    _put(soup, ".card-footnote", "Enquiry only · no payment collected here")
    _put(soup, ".enquiry-surface #enquirySuccess p", "Your enquiry details have been checked.")
    if soup.select_one("#tourExternal"):
        soup.select_one("#tourExternal").decompose()

    # Do not show legacy iQ/Amber source links in a different property's page.
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if any(host in href for host in ("iqstudentaccommodation.com", "amberstudent.com", "my.matterport.com")):
            if "matterport" in href and _text(getattr(p, "tour_url", "")).startswith("https://"):
                link["href"] = _text(p.tour_url)
            else:
                link.decompose()
    query = quote(address or city or name)
    for link in soup.find_all("a", href=True):
        if "google.com/maps" in link["href"]:
            link["href"] = "https://www.google.com/maps/search/?api=1&query=" + query

    # Original amenity card hierarchy stays intact. Only the content changes.
    groups = soup.select_one("#amenities .amenity-groups")
    if groups:
        groups.clear()
        group = soup.new_tag("div", attrs={"class": "amenity-group"})
        title = soup.new_tag("h3")
        title.string = "Property amenities"
        group.append(title)
        options = soup.new_tag("div", attrs={"class": "amenity-list"})
        for value in amenities or ["Facilities to be confirmed with the property team"]:
            span = soup.new_tag("span")
            span.string = value
            options.append(span)
        group.append(options)
        groups.append(group)
    facts = soup.select("#overview .overview-facts > div")
    for index, fact in enumerate(facts):
        if index < len(highlights):
            _put(soup, ".overview-facts > div:nth-child(" + str(index + 1) + ") strong", highlights[index])
            _put(soup, ".overview-facts > div:nth-child(" + str(index + 1) + ") p", "Ask for details")
        elif not preview:
            fact.decompose()

    _details(soup, "#rules .disclosure-list", getattr(p, "policies", []), "Current property policies")
    _details(soup, "#faqList", getattr(p, "faq", []), "What should I confirm before moving in?")

    # Keep the master location explorer layout; never invent distances.
    all_landmarks = soup.select_one("#location .landmark-groups")
    if all_landmarks:
        all_landmarks.clear()
        group = soup.new_tag("div", attrs={"class": "landmark-group"})
        title = soup.new_tag("h3")
        title.string = "Nearby places"
        group.append(title)
        for item in landmarks:
            row = soup.new_tag("div", attrs={"class": "landmark-row"})
            a = soup.new_tag("span")
            a.string = _text(item.get("name"))
            b = soup.new_tag("strong")
            b.string = _text(item.get("detail")) or "Check route"
            row.extend([a, b])
            group.append(row)
        if not landmarks:
            group.append(_paragraph(soup, "Add verified landmarks and distances from the dashboard."))
        all_landmarks.append(group)
    rail = soup.select_one(".rail-nearby-list")
    if rail:
        rail.clear()
        for item in landmarks[:3]:
            row = soup.new_tag("div", attrs={"class": "rail-walk-row"})
            n = soup.new_tag("span")
            n.string = _text(item.get("name"))
            d = soup.new_tag("strong")
            d.string = _text(item.get("detail")) or "Check route"
            row.extend([n, d])
            rail.append(row)
    score = getattr(p, "review_score", None)
    source = _text(getattr(p, "review_source_url", ""))
    if score is None or not source.startswith("https://"):
        for selector in (".property-rating", "#reviews .reviews-summary"):
            el = soup.select_one(selector)
            if el:
                el.decompose()
    else:
        _put(soup, ".property-rating strong", score)
        _put(soup, "#reviews .reviews-score strong", score)
        _put(soup, "#reviews .reviews-summary > div:last-child strong",
             str(getattr(p, "review_count", 0) or 0) + " attributed reviews")
        for el in soup.select("#reviews .reviews-summary a"):
            el["href"] = source
        for el in soup.select(".property-rating a"):
            el["href"] = source
            el.string = str(getattr(p, "review_count", 0) or 0) + " reviews"
    card_box = soup.select_one("#reviews .review-example-grid")
    if card_box:
        card_box.clear()
        for item in reviews:
            card = soup.new_tag("article", attrs={"class": "review-example"})
            person = soup.new_tag("strong")
            person.string = _text(item.get("name")) or "Resident"
            quote_node = _paragraph(soup, _text(item.get("quote")))
            card.extend([person, quote_node])
            card_box.append(card)
        if not reviews:
            card_box.append(_paragraph(soup, "No permissioned resident reviews have been added yet."))
    _put(soup, "#reviews .review-preview-intro p", "Only reviews approved for publication are displayed.")
    _put(soup, "#reviews .review-example-disclosure", "Reviews must be attributable and authorised for publication.")
    # No fixed template pricing, published reviews, or promotional offers should survive.
    for selector in ("#rooms .room-pricing-summary span",):
        pass
    offers = [x for x in _list(getattr(p, "offers", [])) if isinstance(x, dict) and _text(x.get("title"))]
    if offers:
        box = soup.new_tag("div", attrs={"class": "accom-master-offers"})
        for item in offers:
            entry = soup.new_tag("div", attrs={"class": "accom-master-offer"})
            heading = soup.new_tag("strong")
            heading.string = _text(item.get("title"))
            entry.append(heading)
            entry.append(_paragraph(soup, _text(item.get("description"))))
            box.append(entry)
        soup.select_one("#payments").append(box)
    floorplans = [x for x in _list(getattr(p, "floorplans", [])) if isinstance(x, dict) and _safe_image(x.get("url"))]
    if floorplans:
        box = soup.new_tag("div", attrs={"class": "accom-master-floorplans"})
        for item in floorplans:
            img = soup.new_tag("img", attrs={"src": _safe_image(item.get("url")),
                                             "alt": _text(item.get("alt")) or "Floor plan", "loading": "lazy"})
            box.append(img)
        soup.select_one("#floorplan").append(box)

    # These inline styles extend only absent-content/repeater states.
    style = soup.new_tag("style")
    style.string = ".accom-master-preview-note{margin:7px 0 0;padding:8px 13px;color:#725b2b;background:#fff7dd;border-radius:9px;font-size:11px}.accom-master-photo-placeholder{border-radius:18px;background:#f7f7f6;padding:28px;color:#677285}.accom-master-offers,.accom-master-floorplans{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-top:20px}.accom-master-offer{border:1px solid #eee;border-radius:14px;padding:18px;background:#fff}.accom-master-offer strong{color:#ed2024}.accom-master-floorplans img{width:100%;border-radius:13px;object-fit:contain}.room-empty{padding:25px;border-radius:18px;background:white;color:#637184}"
    soup.head.append(style)

    # Essential SSR: visible content and structured data agree with the draft.
    title = soup.head.find("title")
    if title:
        title.string = _text(getattr(p, "seo_title", "")) or name + " | Accom by Emlen"
    for key, value in (("description", _text(getattr(p, "meta_description", "")) or desc[:160]),
                       ("robots", "noindex,nofollow" if preview or demo or bool(getattr(p, "noindex", False))
                        else "index,follow")):
        tag = soup.head.find("meta", attrs={"name": key})
        if not tag:
            tag = soup.new_tag("meta", attrs={"name": key})
            soup.head.append(tag)
        tag["content"] = value
    canonical = soup.new_tag("link", attrs={"rel": "canonical",
        "href": public_site_url.rstrip("/") + "/property/" + quote(_text(getattr(p, "slug", "")))})
    soup.head.append(canonical)
    schema = {"@context": "https://schema.org", "@type": "ApartmentComplex", "name": name,
              "address": {"@type": "PostalAddress", "streetAddress": _text(getattr(p, "address", "")),
                          "addressLocality": city, "addressCountry": _text(getattr(p, "country", ""))}}
    ld = soup.new_tag("script", attrs={"type": "application/ld+json"})
    ld.string = json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c")
    soup.head.append(ld)
    data = dict(payload)
    data.update({"name": name, "description": desc, "gallery": photos, "preview": bool(preview), "is_demo": demo})
    # Embedded original sample imagery is used for unfilled admin previews only.
    if preview and not photos:
        data["gallery"] = []
    script = soup.new_tag("script", attrs={"type": "application/json", "id": "accom-property-data"})
    script.string = json.dumps(data, ensure_ascii=False, default=str).replace("<", "\\u003c")
    soup.head.append(script)
    # The external original script is CSP-compatible; retain all original behavior.
    # The server preview never submits enquiries. The public integration handles POST.
    bridge = soup.new_tag("script", attrs={"src": "/accom-template/original-integration.js", "defer": ""})
    soup.body.append(bridge)
    return str(soup).replace('content="index,follow" name="robots"', 'name="robots" content="index,follow"').replace('content="noindex,nofollow" name="robots"', 'name="robots" content="noindex,nofollow"')
