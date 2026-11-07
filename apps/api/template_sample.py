"""Unpublished Accom page samples extracted from the approved master template.

These are *illustrative and unverified*, not facts about a newly created property.
They are offered to the editor only; opening a draft never writes to the DB.
"""
from functools import lru_cache
from pathlib import Path
import re
from bs4 import BeautifulSoup

MASTER = Path(__file__).with_name("property_master.html")
ASSETS = "/accom-template/assets/"

@lru_cache(maxsize=1)
def template_sample():
    soup = BeautifulSoup(MASTER.read_text(encoding="utf-8"), "html.parser")
    def text(selector):
        element = soup.select_one(selector)
        return element.get_text(" ", strip=True) if element else ""
    city = text(".crumbs a[href='#location']")
    full_address = text(".property-address")
    postcode_match = re.search(r"\b[A-Z]{1,2}[0-9][A-Z0-9]?\s*[0-9][A-Z]{2}\b", full_address, re.I)
    postcode = postcode_match.group(0).upper() if postcode_match else ""
    address = full_address
    if postcode:
        address = re.sub(r",?\s*" + re.escape(postcode) + r"\s*$", "", address, flags=re.I)
    if city and address.endswith(", " + city):
        # Match the master template's own conventional property address layout.
        address = address[:-(len(city) + 2)]
    facts = soup.select("#overview .overview-facts > div")
    amenities = [item.get_text(" ", strip=True) for item in soup.select("#amenities .amenity-list span")]
    def qa(selector):
        result = []
        for entry in soup.select(selector):
            title = entry.select_one("summary")
            paragraph = entry.select_one("p")
            if title and paragraph:
                # The disclosure's plus sign belongs to the control, not its text.
                question = title.get_text(" ", strip=True).rstrip(" +").strip()
                if question:
                    result.append({"question": question, "answer": paragraph.get_text(" ", strip=True)})
        return result
    landmarks = []
    for node in soup.select("#location .landmark-row"):
        label = node.select_one("span")
        detail = node.select_one("strong")
        if label:
            landmarks.append({"name": label.get_text(" ", strip=True),
                              "detail": detail.get_text(" ", strip=True) if detail else ""})
    # These are the same illustrative, local assets the approved demo seed uses.
    # Do not substitute real listing photos or invent an image source.
    photo_specs = [
        ("ensuite.webp", "Furnished en suite room"),
        ("lounge.webp", "Shared lounge"),
        ("studio.webp", "Studio room"),
        ("study.webp", "Shared study space"),
    ]
    gallery = [
        {"url": ASSETS + filename,
         "alt": "Illustrative " + label + " — not a verified property photograph",
         "category": "Rooms" if i in (0, 2) else "Shared spaces",
         "layout": "large" if i == 0 else "regular"}
        for i, (filename, label) in enumerate(photo_specs)
    ]
    university = next((item["name"] for item in landmarks if "University" in item["name"]), "")
    return {
        "city": city, "country": "United Kingdom", "address": address,
        "postcode": postcode, "university": university,
        "description": text("#overview .intro-text"),
        "highlights": [f.select_one("strong").get_text(" ", strip=True) for f in facts if f.select_one("strong")],
        "highlight_descriptions": [f.select_one("p").get_text(" ", strip=True) if f.select_one("p") else "" for f in facts if f.select_one("strong")],
        "amenities": amenities,
        "gallery": gallery,
        "policies": qa("#rules .disclosure-list details"),
        "faq": qa("#faqList details"),
        "landmarks": landmarks,
    }

def should_autofill_template(p):
    """Only untouched demonstrator drafts get unverified example data automatically."""
    name = str(getattr(p, "name", ""))
    if getattr(p, "published", False):
        return False
    if not (bool(getattr(p, "is_demo", False)) or re.fullmatch(r"demo[ _-]*[0-9]+", name, flags=re.I)):
        return False
    return not any(str(getattr(p, field, "") or "").strip() for field in ("city", "address", "university", "postcode"))
