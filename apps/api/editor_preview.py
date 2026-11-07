"""Authenticated, non-persistent HTML previews for the approved Accom property template.

Never writes listing state or enables booking/enquiry submission. Only fields
used by the trusted built-in template are copied from an editor draft.
"""
from types import SimpleNamespace
import re
from original_runtime import render_property

TEXT_FIELDS = {
    'name', 'city', 'country', 'address', 'postcode', 'university',
    'description', 'seo_title', 'meta_description', 'review_source_url', 'tour_url',
}
COLLECTIONS = {
    'highlights', 'amenities', 'policies', 'faq', 'landmarks',
    'gallery', 'floorplans', 'offers', 'reviews',
}
WEB_IMAGE = re.compile(r'^https://[^\s<>"\']+$', re.I)
LOCAL_IMAGE = re.compile(r'^/(?:api/media/[1-9][0-9]*|accom-template/assets/[a-z0-9_-]+\.(?:webp|jpg|png))$', re.I)


def _draft_list(key, value):
    if not isinstance(value, list):
        return []
    result = []
    for item in value[:80]:
        if key in ('highlights', 'amenities'):
            if isinstance(item, str) and item.strip():
                result.append(item[:350])
            continue
        if not isinstance(item, dict):
            continue
        if key in ('gallery', 'floorplans'):
            url = str(item.get('url') or '').strip()
            if not (WEB_IMAGE.fullmatch(url) or LOCAL_IMAGE.fullmatch(url)):
                continue
            result.append({
                'url': url[:2048], 'alt': str(item.get('alt') or '')[:240],
                'category': str(item.get('category') or 'Photos')[:100],
                'layout': 'large' if item.get('layout') == 'large' else 'regular',
            })
            continue
        record = {}
        expected = {
            'policies': ('question', 'answer'),
            'faq': ('question', 'answer'),
            'landmarks': ('name', 'detail'),
            'offers': ('title', 'description', 'valid_until'),
            'reviews': ('name', 'quote', 'source_url'),
        }.get(key, ())
        for field in expected:
            record[field] = str(item.get(field) or '')[:3500]
        if any(record.values()):
            result.append(record)
    return result


def render_draft(property_record, changes, snapshot, public_site_url):
    if not isinstance(changes, dict):
        changes = {}
    fields = (TEXT_FIELDS | COLLECTIONS | {'slug', 'noindex', 'is_demo', 'review_score', 'review_count', 'content_overrides'})
    transient = SimpleNamespace(**{key: getattr(property_record, key, None) for key in fields})
    for key in TEXT_FIELDS:
        value = changes.get(key)
        if isinstance(value, str):
            setattr(transient, key, value[:3500])
    for key in COLLECTIONS:
        if key in changes:
            setattr(transient, key, _draft_list(key, changes[key]))
    if isinstance(changes.get('content_overrides'), dict):
        transient.content_overrides = dict(list(changes['content_overrides'].items())[:600])
    if isinstance(changes.get('is_demo'), bool):
        transient.is_demo = changes['is_demo']
    if isinstance(changes.get('noindex'), bool):
        transient.noindex = changes['noindex']
    for key in ('review_score', 'review_count'):
        value = changes.get(key)
        if value is None or isinstance(value, (int, float)):
            setattr(transient, key, value)
    snapshot = dict(snapshot)
    for key in fields:
        if hasattr(transient, key) and key not in ('slug',):
            snapshot[key] = getattr(transient, key)
    return render_property(transient, snapshot, public_site_url, preview=True)
