/* Integration for the approved Accom master.
 * Preserve its original layout, gallery, navigation and comparison behavior.
 * Enquiry POSTs are disabled for staff previews and enabled only on published pages.
 */
(() => {
  'use strict';
  const dataNode = document.getElementById('accom-property-data');
  if (!dataNode) return;
  let listing;
  try { listing = JSON.parse(dataNode.textContent || '{}'); } catch { return; }
  const form = document.getElementById('enquiryForm');
  if (!form) return;
  const showError = message => {
    const node = document.getElementById('enquiryError');
    if (node) { node.hidden = false; node.textContent = message; }
  };
  form.addEventListener('submit', async event => {
    event.preventDefault();
    event.stopImmediatePropagation();
    const inputs = new FormData(form);
    const name = String(inputs.get('name') || '').trim();
    const email = String(inputs.get('email') || '').trim();
    const consent = inputs.get('consent') !== null;
    if (!name || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || !consent) {
      showError('Enter a valid name, email and consent before submitting.');
      return;
    }
    const button = form.querySelector('button[type=submit]');
    if (button) button.disabled = true;
    try {
      if (!listing.preview) {
        const room = document.querySelector('.room-card.selected-room');
        const roomId = room && /^\d+$/.test(room.dataset.room || '') ? Number(room.dataset.room) : null;
        const response = await fetch('/api/enquiries', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            property_id: listing.id,
            room_id: roomId,
            name, email, consent,
            phone: String(inputs.get('phone') || '').trim(),
            message: String(inputs.get('message') || '').trim()
          })
        });
        if (!response.ok) {
          let message = 'Could not submit the enquiry. Please try again.';
          try {
            const result = await response.json();
            if (typeof result.detail === 'string') message = result.detail;
          } catch {}
          throw Error(message);
        }
      }
      form.hidden = true;
      const success = document.getElementById('enquirySuccess');
      if (success) {
        success.hidden = false;
        const heading = success.querySelector('h3');
        const text = success.querySelector('p');
        if (heading) heading.textContent = listing.preview ? 'Preview validation successful' : 'Enquiry sent';
        if (text) text.textContent = listing.preview
          ? 'This is a staff-only preview. No enquiry was transmitted.'
          : 'Your request has been sent to Accom. No booking or payment has been made.';
      }
    } catch (error) {
      showError(error instanceof Error ? error.message : 'Could not submit the enquiry.');
    } finally {
      if (button) button.disabled = false;
    }
  }, true);
})();
