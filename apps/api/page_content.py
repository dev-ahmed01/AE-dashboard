"""Stable, safe content-field mapping for the original 13-section Accom template.

The approved HTML remains the source of truth. Only text nodes and safe URL/
accessibility attributes are exposed; nested markup, scripts and controls are
never replaced by user-supplied HTML.
"""
import re
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

SECTIONS = [
    ("top", "Hero & gallery"),
    ("overview", "Residence overview"),
    ("about", "Property details"),
    ("tours", "Photo categories & tour"),
    ("amenities", "Amenities & bills"),
    ("rooms", "Rooms & price choices"),
    ("rules", "House rules"),
    ("payments", "Payments & fees"),
    ("floorplan", "Floor plans"),
    ("neighbourhood", "Neighbourhood"),
    ("faqs", "Frequently asked questions"),
    ("location", "Landmarks & location"),
    ("reviews", "Student reviews"),
]
_SECTION_IDS = {key for key, _ in SECTIONS}
TEXT_TAGS = frozenset(("h1", "h2", "h3", "h4", "h5", "h6", "p", "span", "strong", "em", "small",
                       "a", "button", "label", "summary", "li", "div", "time", "figcaption"))
DYNAMIC_GROUPS = frozenset(("amenity-groups", "overview-facts", "disclosure-list", "landmark-groups",
                             "review-example-grid", "accom-master-offers", "accom-master-floorplans",
                             "room-card", "room-list", "photo-category-grid", "rail-nearby-list"))
SKIP_PARENTS = frozenset(("script", "style", "svg", "noscript", "template", "textarea", "select", "option"))
IMAGE_URL = re.compile(r"^(https://[^\s<>\"']+|/(?:api/media/[0-9]+|accom-template/assets/[a-zA-Z0-9_-]+\.(?:webp|jpg|jpeg|png)))$")
LINK_URL = re.compile(r"^(https://[^\s<>\"']+|/(?!/)[^\s<>\"']*|#[^\s<>\"']*|mailto:[^\s<>\"']+|tel:[+0-9 ()-]+)$", re.I)



# Explicitly approved content fields. Navigation, breadcrumbs, technical UI,
# pricing calculations and gallery controls are *not* page content fields.
# The schema keys remain stable even when the template's DOM changes.
SECTION_FIELDS = [
    # property name, city, address and gallery are structured Property fields.
    ("top", "hero.eyebrow", "Property category", ".property-tag", "text", "Property details", 0),
    ("top", "hero.room_cta", "View rooms button", "#railRooms", "cta_label", "Page actions", 0),
    ("top", "hero.enquiry_cta", "Enquiry button", ".booking-card .rail-controls [data-enquire]", "cta_label", "Page actions", 0),
    ("overview", "overview.title", "Section heading", "#overview > h2", "text", "Headings & copy", 0),
    ("about", "about.title", "Section heading", "#about h2", "text", "Headings & copy", 0),
    ("about", "about.detail_1", "Property description · paragraph 1", "#about .story-detail", "textarea", "Headings & copy", 0),
    ("about", "about.detail_2", "Property description · paragraph 2", "#about .story-detail", "textarea", "Headings & copy", 1),
    ("about", "about.room_guide_title", "Room guide heading", "#about .story-room-guide h3", "text", "Room guide", 0),
    ("about", "about.room_guide_note", "Room guide description", "#about .story-guide-note", "textarea", "Room guide", 0),
    ("about", "about.rooms_cta_label", "Explore room types · button text", "#about .story-secondary-link", "cta_label", "Call to action", 0),
    ("about", "about.rooms_cta_link", "Explore room types · destination", "#about .story-secondary-link", "cta_link", "Call to action", 0),
    ("tours", "tours.title", "Section heading", "#tours h2", "text", "Headings & copy", 0),
    ("tours", "tours.description", "Section description", "#tours .section-intro", "textarea", "Headings & copy", 0),
    ("amenities", "amenities.title", "Section heading", "#amenities > h2", "text", "Headings & copy", 0),
    ("amenities", "amenities.bills_title", "Bills calculator heading", "#amenities .bill-estimate-top h3", "text", "Bills calculator", 0),
    ("amenities", "amenities.bills_intro", "Bills calculator explanation", "#amenities .bill-estimate-top p", "textarea", "Bills calculator", 0),
    ("rooms", "rooms.title", "Section heading", "#rooms h2", "text", "Headings & copy", 0),
    ("rooms", "rooms.description", "Section description", "#rooms .section-title-row p", "textarea", "Headings & copy", 0),
    ("rules", "rules.title", "Section heading", "#rules > h2", "text", "Headings & copy", 0),
    ("payments", "payments.title", "Section heading", "#payments > h2", "text", "Headings & copy", 0),
    ("floorplan", "floorplan.title", "Section heading", "#floorplan > h2", "text", "Headings & copy", 0),
    ("floorplan", "floorplan.card_title", "Request card heading", "#floorplan .inline-request strong", "text", "Request card", 0),
    ("floorplan", "floorplan.card_description", "Request card description", "#floorplan .inline-request p", "textarea", "Request card", 0),
    ("floorplan", "floorplan.cta_label", "Request floor plan · button text", "#floorplan [data-enquire]", "cta_label", "Call to action", 0),
    ("neighbourhood", "neighbourhood.title", "Section heading", "#neighbourhood > h2", "text", "Headings & copy", 0),
    ("neighbourhood", "neighbourhood.description", "Neighbourhood description", "#neighbourhood .neighbourhood-layout p", "textarea", "Headings & copy", 0),
    ("neighbourhood", "neighbourhood.photo", "Neighbourhood image", "#neighbourhood .neighbourhood-layout img", "image", "Section image", 0),
    ("neighbourhood", "neighbourhood.photo_alt", "Neighbourhood image description", "#neighbourhood .neighbourhood-layout img", "image_alt", "Section image", 0),
    ("neighbourhood", "neighbourhood.cta_label", "View area · CTA text", "#neighbourhood a.source-link", "cta_label", "Call to action", 0),
    ("neighbourhood", "neighbourhood.cta_link", "View area · destination", "#neighbourhood a.source-link", "cta_link", "Call to action", 0),
    ("faqs", "faqs.title", "Section heading", "#faqs > h2", "text", "Headings & copy", 0),
    ("location", "location.title", "Section heading", "#location > h2", "text", "Headings & copy", 0),
    ("location", "location.description", "Landmarks introduction", "#location > .section-intro", "textarea", "Headings & copy", 0),
    ("location", "location.cta_label", "Get directions · CTA text", "#location a.source-link", "cta_label", "Call to action", 0),
    ("location", "location.cta_link", "Get directions · destination", "#location a.source-link", "cta_link", "Call to action", 0),
    ("reviews", "reviews.title", "Section heading", "#reviews > h2", "text", "Headings & copy", 0),
    ("reviews", "reviews.subheading", "Reviews introduction heading", "#reviews .review-preview-intro h3", "text", "Headings & copy", 0),
]
for index in range(4):
    SECTION_FIELDS.extend([
        ("payments", f"payments.card_{index + 1}.title", f"Payment card {index + 1} · title",
         "#payments .payments-grid > div strong", "text", "Payment cards", index),
        ("payments", f"payments.card_{index + 1}.description", f"Payment card {index + 1} · description",
         "#payments .payments-grid > div p", "textarea", "Payment cards", index),
    ])

FIELD_BY_KEY = {item[1]: item for item in SECTION_FIELDS}


def _find_field_node(soup, spec):
    matches = soup.select(spec[3])
    return matches[spec[6]] if len(matches) > spec[6] else None


def _field_value(node, kind):
    if kind == "cta_link":
        return node.get("href", "")
    if kind == "image":
        src = node.get("src", "")
        return src if IMAGE_URL.fullmatch(src) else ""
    if kind == "image_alt":
        return node.get("alt", "")
    return node.get_text(" ", strip=True)


def _replace_text(node, value):
    # Replace text only, preserving icons, event hooks and the original frame.
    children = [child for child in node.contents if isinstance(child, NavigableString)
                and not isinstance(child, Comment) and str(child).strip()]
    if children:
        children[0].replace_with(value)
        for child in children[1:]:
            child.replace_with("")
    else:
        node.append(NavigableString(value))


def _approved_structured(spec, value):
    kind = spec[4]
    if not isinstance(value, str) or len(value) > 2500:
        return False
    if kind == "cta_link":
        return len(value) <= 2048 and bool(LINK_URL.fullmatch(value))
    if kind == "image":
        return not value or (len(value) <= 2048 and bool(IMAGE_URL.fullmatch(value)))
    if kind == "image_alt":
        return len(value) <= 240
    return True


def _apply_structured_field(node, kind, value):
    if kind == "cta_link":
        node["href"] = value
        if value.startswith("https://"):
            node["rel"] = "noopener noreferrer"
        return
    if kind == "image":
        if not value:
            node["src"] = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
        else:
            node["src"] = value
        node.attrs.pop("data-asset", None)
        return
    if kind == "image_alt":
        node["alt"] = value
        return
    _replace_text(node, value)


def _structured_fields(soup):
    for spec in SECTION_FIELDS:
        node = _find_field_node(soup, spec)
        if node is None:
            continue
        section, key, label, selector, kind, group, index = spec
        yield {"key": key, "section": section, "kind": kind, "label": label,
               "group": group, "value": _field_value(node, kind)}, node, spec


def _section(tag):
    for ancestor in [tag, *tag.parents]:
        if isinstance(ancestor, Tag) and ancestor.get("id") in _SECTION_IDS:
            return ancestor["id"]
    return "top"


def _ignored(tag):
    for ancestor in [tag, *tag.parents]:
        if not isinstance(ancestor, Tag):
            continue
        if ancestor.name in SKIP_PARENTS:
            return True
        if ancestor.get("hidden") is not None or ancestor.get("aria-hidden") == "true":
            return True
        if DYNAMIC_GROUPS.intersection(ancestor.get("class", [])):
            return True
    return False


def _path(tag):
    steps = []
    current = tag
    while isinstance(current, Tag) and current.name not in ("html", "body"):
        ident = current.get("id")
        if ident and re.fullmatch(r"[A-Za-z][\w-]*", ident):
            steps.append("#" + ident)
            break
        position = 1 + sum(1 for previous in current.previous_siblings
                           if isinstance(previous, Tag) and previous.name == current.name)
        steps.append(f"{current.name}:nth-of-type({position})")
        current = current.parent
    return " > ".join(reversed(steps))


def _label(tag, value, kind):
    context = re.sub(r"\s+", " ", tag.get_text(" ", strip=True))[:65]
    if kind == "src":
        return "Image URL — " + (tag.get("alt") or "Property photo")[:55]
    if kind == "alt":
        return "Image description"
    if kind == "href":
        return "Link destination — " + (context or "Link")[:55]
    role = {"h1": "Main heading", "h2": "Section heading", "h3": "Heading",
            "p": "Paragraph", "button": "Button", "a": "Link label",
            "strong": "Emphasis", "span": "Label"}.get(tag.name, "Text")
    return role + " — " + re.sub(r"\s+", " ", str(value))[:65]


def iter_fields(soup):
    """Yield the exact DOM node associated with each editable value."""
    root = soup.body
    if not root:
        return
    for tag in root.find_all(True):
        if _ignored(tag):
            continue
        path = _path(tag)
        section = _section(tag)
        if tag.name in TEXT_TAGS:
            for slot, node in enumerate(tag.contents):
                if not isinstance(node, NavigableString) or isinstance(node, Comment):
                    continue
                value = str(node).strip()
                if len(value) < 2 or len(value) > 2500:
                    continue
                yield {"key": path + "|text:" + str(slot), "section": section,
                       "kind": "text", "label": _label(tag, value, "text"),
                       "value": value}, tag, node
        if tag.name == "a" and tag.get("href"):
            value = str(tag["href"])
            if LINK_URL.fullmatch(value):
                yield {"key": path + "|href", "section": section,
                       "kind": "href", "label": _label(tag, value, "href"),
                       "value": value}, tag, None
        if tag.name == "img":
            for attr in ("src", "alt"):
                value = str(tag.get(attr) or "")
                if not value or (attr == "src" and not IMAGE_URL.fullmatch(value)):
                    continue
                yield {"key": path + "|" + attr, "section": section,
                       "kind": attr, "label": _label(tag, value, attr),
                       "value": value}, tag, None


def _approved(kind, value):
    if not isinstance(value, str) or len(value) > 2500:
        return False
    if kind == "src":
        return len(value) <= 2048 and bool(IMAGE_URL.fullmatch(value))
    if kind == "href":
        return len(value) <= 2048 and bool(LINK_URL.fullmatch(value))
    if kind == "alt":
        return len(value) <= 240
    return True


def apply_overrides(soup, values):
    """Overlay saved edits after standard listing data is projected into the master."""
    if not isinstance(values, dict):
        return
    safe = dict(list(values.items())[:600])
    for field, tag, node in iter_fields(soup):
        value = safe.get(field["key"])
        if not _approved(field["kind"], value):
            continue
        kind = field["kind"]
        if kind == "text":
            original = str(node)
            before = re.match(r"^\s*", original).group()
            after = re.search(r"\s*$", original).group()
            node.replace_with(before + value + after)
        else:
            tag[kind] = value


    # New semantic fields are restricted to clearly identified page elements.
    for field, node, spec in _structured_fields(soup):
        value = safe.get(field["key"])
        if value is not None and _approved_structured(spec, value):
            _apply_structured_field(node, field["kind"], value)


def describe(html):
    """The admin always receives current, prefilled values from its actual rendered DOM."""
    soup = BeautifulSoup(html, "html.parser")
    groups = [{"id": ident, "title": title, "fields": []} for ident, title in SECTIONS]
    by_id = {group["id"]: group for group in groups}
    for field, _, _ in _structured_fields(soup):
        by_id[field["section"]]["fields"].append(field)
    return groups


def valid_overrides(values):
    if not isinstance(values, dict) or len(values) > 600:
        raise ValueError("Too many page-copy fields")
    for key, value in values.items():
        if not isinstance(key, str) or len(key) > 500:
            raise ValueError("Invalid page-copy field identifier")
        if key in FIELD_BY_KEY:
            if not _approved_structured(FIELD_BY_KEY[key], value):
                raise ValueError("Invalid section field value or CTA destination")
            continue
        # Preserve old saved page values for existing drafts, without exposing
        # incidental navigation links in the new structured editor.
        if not re.fullmatch(r"[\w#:. >()-]+\|(text:[0-9]+|href|src|alt)", key):
            raise ValueError("Invalid legacy page-copy field identifier")
        kind = key.rsplit("|", 1)[-1].split(":", 1)[0]
        if not _approved(kind, value):
            raise ValueError("Invalid page-copy value or URL")
    return values
