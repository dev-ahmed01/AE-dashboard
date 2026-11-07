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


def describe(html):
    """The admin always receives current, prefilled values from its actual rendered DOM."""
    soup = BeautifulSoup(html, "html.parser")
    groups = [{"id": ident, "title": title, "fields": []} for ident, title in SECTIONS]
    by_id = {group["id"]: group for group in groups}
    for field, _, _ in iter_fields(soup):
        by_id[field["section"]]["fields"].append(field)
    return groups


def valid_overrides(values):
    if not isinstance(values, dict) or len(values) > 600:
        raise ValueError("Too many page-copy fields")
    for key, value in values.items():
        if not isinstance(key, str) or len(key) > 500 or not re.fullmatch(r"[\w#:. >()-]+\|(text:[0-9]+|href|src|alt)", key):
            raise ValueError("Invalid page-copy field identifier")
        kind = key.rsplit("|", 1)[-1].split(":", 1)[0]
        if not _approved(kind, value):
            raise ValueError("Invalid page-copy value or URL")
    return values
