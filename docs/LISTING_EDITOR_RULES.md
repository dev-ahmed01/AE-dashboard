# Accom listing editor — repeaters and image layout

The Accom admin editor follows the repeatable-content interaction pattern used by Dashboard-WE, adapted to **structured accommodation records** rather than imported HTML nodes.

## Repeater rule

Any known repeating property group is editable as an ordered collection, even when it currently has fewer than three items. This covers highlights, amenities, property photos, floor plans, FAQs, policies, nearby landmarks, offers and reviews. Every group offers **Add another**, Edit, Move up, Move down and Remove, with immediate local editing. Existing listings are read as arrays, so the current property data is preserved.

For new or imported unrecognized HTML templates in the future, the WE discovery rule of recognizing three or more similar sibling nodes remains a separate potential capability. The Accom dashboard does not yet implement WE-style arbitrary HTML template import.

Rooms remain separate database records with a dedicated **Add room** operation, because rent and availability should not be saved as unstructured page fields.

## Picture layout

Each gallery image is stored as an object:
```json
{"url":"https://example.com/room.webp","alt":"En suite bedroom","category":"Rooms","layout":"regular"}
```

The **Regular** setting uses one gallery mosaic cell; **Large** spans two columns and two rows. The per-image switch works without changing the original image dimensions. Changes appear immediately in the editor's layout preview and, once saved, in the public listing gallery. The responsive layout retains regular/large distinctions on mobile.

Legacy images without a layout default to the large leading hero photo and regular subsequent photos when loaded into the editor. Once saved, the explicit layout is retained.

The backend rejects any layout other than `regular` or `large`, and accepts only HTTP(S) image URLs. It preserves image alt text, category and ordering in PostgreSQL's JSON fields.

## Checkpoints

- Add three or more highlights, reorder and delete; save and reload.
- Add FAQs, policies, landmarks, offers and reviews; verify the corresponding public listing sections.
- Add multiple photos, select Regular/Large independently, and compare the preview to the public property gallery on desktop and mobile.
- Confirm unsafe image URLs and unsupported layout values return HTTP 422.
- Verify existing properties without new layout metadata still render; avoid assuming an imported image is licensed or verified.

**Current limitation:** Property images are entered as approved remote URLs. Direct local-file upload and a production media library remain a separate task.
