import { faqs, filterRooms, formatMoney, media, policies, readInquiryValues, rooms, totalRent, validateInquiry } from './data.js';

const state = {
  category: 'all',
  compareIds: [],
  galleryIndex: 0,
  selectedRoomId: null,
  tenancies: Object.fromEntries(rooms.map((room) => [room.id, 0])),
};

const $ = (selector, scope = document) => scope.querySelector(selector);
const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];
const selectedRoom = () => rooms.find((room) => room.id === state.selectedRoomId);
const selectedTenancy = (room = selectedRoom()) => room.tenancies[state.tenancies[room.id]];
const announce = (message) => { $('#live-region').textContent = message; };

function roomTemplate(room) {
  const tenancy = room.tenancies[state.tenancies[room.id]];
  const isSelected = room.id === state.selectedRoomId;
  const isCompared = state.compareIds.includes(room.id);
  return `
    <article class="room-row${isSelected ? ' selected' : ''}" data-room-id="${room.id}">
      <div class="room-summary">
        <img class="room-thumb" src="${room.image}" width="1536" height="1024" loading="lazy" alt="Illustrative view for ${room.name}">
        <div>
          <div class="room-name-line"><h3>${room.name}</h3><span class="room-category">${room.category}</span></div>
          <div class="room-meta"><span>${room.area}</span><span>${room.bathroom}</span><span>${room.kitchen}</span></div>
        </div>
        <div class="room-price"><strong>${formatMoney(tenancy.weekly)}</strong><span>/ week</span></div>
      </div>
      <div class="room-actions">
        <label class="compare-toggle"><input type="checkbox" data-compare-room="${room.id}" ${isCompared ? 'checked' : ''}> Add to comparison</label>
        <button class="select-room" type="button" data-select-room="${room.id}">${isSelected ? 'Selected room' : 'Select this room'}</button>
      </div>
      <details class="room-details">
        <summary>Room details & tenancy options</summary>
        <dl class="room-details-grid">
          <div><dt>Privacy</dt><dd>${room.privacy}</dd></div>
          <div><dt>Included in room</dt><dd>${room.inclusions.join(', ')}</dd></div>
          <div class="tenancy-choice">
            ${room.tenancies.map((option, index) => `
              <label>
                <input type="radio" name="tenancy-${room.id}" value="${index}" data-tenancy-room="${room.id}" ${index === state.tenancies[room.id] ? 'checked' : ''}>
                <strong>${option.weeks} weeks · ${formatMoney(option.weekly)}/week</strong>
                <span>${option.start} – ${option.end} · total ${formatMoney(totalRent(option.weekly, option.weeks))}</span>
              </label>`).join('')}
          </div>
        </dl>
        <p class="room-provenance">${room.provenance.label}</p>
      </details>
    </article>`;
}

function renderRooms() {
  const visible = filterRooms(rooms, state.category);
  $('#room-list').innerHTML = visible.length ? visible.map(roomTemplate).join('') : '<p>No rooms in this category. Clear the filter to compare all demo rooms.</p>';
  updateCompareButton();
}

function updateSelectedRoom() {
  const cheapest = Math.min(...rooms.flatMap(room => room.tenancies.map(option => option.weekly)));
  const startingPrice = formatMoney(cheapest);
  $('#cta-from-price').textContent = startingPrice;
  const room = selectedRoom();
  $('#cta-first-visit').hidden = Boolean(room);
  $('#cta-selected-details').hidden = !room;
  if (!room) {
    $('#mobile-room').textContent = 'No room selected';
    $('#mobile-price').textContent = `From ${startingPrice}/wk`;
    $('#mobile-commitment').textContent = 'Explore rooms · demo prices';
    $('#mobile-main-action').textContent = 'View rooms';
    $('#cta-enquire-button').textContent = 'Ask about this property';
    return;
  }
  const tenancy = selectedTenancy(room);
  $('#cta-room-name').textContent = room.name;
  $('#cta-weekly').textContent = formatMoney(tenancy.weekly);
  $('#cta-tenancy').textContent = `${tenancy.weeks} weeks · ${tenancy.start}`;
  $('#cta-total').textContent = formatMoney(totalRent(tenancy.weekly, tenancy.weeks));
  $('#mobile-room').textContent = room.name;
  $('#mobile-price').textContent = `${formatMoney(tenancy.weekly)}/wk`;
  $('#mobile-commitment').textContent = `${tenancy.weeks} weeks · ${formatMoney(totalRent(tenancy.weekly, tenancy.weeks))} total · demo`;
  $('#mobile-main-action').textContent = 'Enquire';
  $('#cta-enquire-button').textContent = 'Enquire about selected room';
}

function updateCompareButton() {
  // Compare state remains functional, without a visible or announced count.
  const control = $('#open-compare');
  const ready = state.compareIds.length === 2;
  control.setAttribute('aria-label', ready ? 'Compare selected rooms' : 'Compare rooms');
  control.dataset.ready = String(ready);
}

function renderAccordions() {
  $('#policy-list').innerHTML = policies.map((item) => `<details><summary>${item.title}</summary><p>${item.body}</p></details>`).join('');
  $('#faq-list').innerHTML = faqs.map(([question, answer]) => `<details><summary>${question}</summary><p>${answer}</p></details>`).join('');
}

function setGalleryImage(index) {
  state.galleryIndex = (index + media.length) % media.length;
  const item = media[state.galleryIndex];
  const image = $('#lightbox-image');
  image.src = item.src;
  image.alt = item.alt;
  $('#lightbox-caption').textContent = `${item.category} · ${state.galleryIndex + 1} of ${media.length} · illustrative prototype media`;
  $$('#gallery-thumbs button').forEach((button, buttonIndex) => {
    button.classList.toggle('active', buttonIndex === state.galleryIndex);
    button.setAttribute('aria-current', buttonIndex === state.galleryIndex ? 'true' : 'false');
  });
}

function openGallery(index = 0) {
  const dialog = $('#gallery-dialog');
  if (!dialog.open) dialog.showModal();
  setGalleryImage(index);
}

function setupGallery() {
  $('#gallery-thumbs').innerHTML = media.map((item, index) => `<button type="button" data-thumb-index="${index}" aria-label="Show ${item.category} image"><img src="${item.src}" width="120" height="80" alt=""></button>`).join('');
  $$('.gallery-tile').forEach((button) => button.addEventListener('click', () => openGallery(Number(button.dataset.galleryIndex))));
  $('#view-gallery').addEventListener('click', () => openGallery(0));
  $('#gallery-prev').addEventListener('click', () => setGalleryImage(state.galleryIndex - 1));
  $('#gallery-next').addEventListener('click', () => setGalleryImage(state.galleryIndex + 1));
  $('#gallery-thumbs').addEventListener('click', (event) => {
    const button = event.target.closest('[data-thumb-index]');
    if (button) setGalleryImage(Number(button.dataset.thumbIndex));
  });
  $('#gallery-dialog').addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft') setGalleryImage(state.galleryIndex - 1);
    if (event.key === 'ArrowRight') setGalleryImage(state.galleryIndex + 1);
  });
  let touchStart = null;
  $('.lightbox-stage').addEventListener('pointerdown', (event) => { touchStart = event.clientX; });
  $('.lightbox-stage').addEventListener('pointerup', (event) => {
    const start = touchStart;
    touchStart = null;
    if (start === null || Math.abs(event.clientX - start) < 55) return;
    setGalleryImage(state.galleryIndex + (event.clientX < start ? 1 : -1));
  });
  $('.lightbox-stage').addEventListener('pointercancel', () => { touchStart = null; });
}

function renderComparison() {
  const compared = state.compareIds.map((id) => rooms.find((room) => room.id === id));
  if (compared.length !== 2) return;
  const row = (label, values) => `<tr><th scope="row">${label}</th>${values.map((value) => `<td>${value}</td>`).join('')}</tr>`;
  $('#comparison-table').innerHTML = `<table class="comparison-grid">
    <caption class="sr-only">Comparison of ${compared[0].name} and ${compared[1].name}</caption>
    <thead><tr><th scope="col">Room</th>${compared.map((room) => `<th scope="col" class="compare-head"><img src="${room.image}" width="1536" height="1024" alt=""><span>${room.name}</span></th>`).join('')}</tr></thead>
    <tbody>
      ${row('Privacy', compared.map((room) => room.privacy))}
      ${row('Kitchen', compared.map((room) => room.kitchen))}
      ${row('Bathroom', compared.map((room) => room.bathroom))}
      ${row('Area', compared.map((room) => room.area))}
      ${row('Selected tenancy', compared.map((room) => { const tenancy = selectedTenancy(room); return `${tenancy.weeks} weeks<br>${tenancy.start}`; }))}
      ${row('Weekly price', compared.map((room) => `<strong>${formatMoney(selectedTenancy(room).weekly)}</strong> <small>demo</small>`))}
      ${row('Illustrative total', compared.map((room) => { const tenancy = selectedTenancy(room); return `<strong>${formatMoney(totalRent(tenancy.weekly, tenancy.weeks))}</strong>`; }))}
    </tbody>
  </table>`;
}

function setupRoomInteractions() {
  $('.filter-group').addEventListener('click', (event) => {
    const button = event.target.closest('[data-filter]');
    if (!button) return;
    state.category = button.dataset.filter;
    $$('.filter-group button').forEach((item) => {
      const active = item === button;
      item.classList.toggle('active', active);
      item.setAttribute('aria-pressed', String(active));
    });
    renderRooms();
  });

  $('#explain-types').addEventListener('click', () => {
    const explainer = $('#room-type-explainer');
    explainer.hidden = !explainer.hidden;
    $('#explain-types').textContent = explainer.hidden ? 'Ensuite or studio?' : 'Hide room explanation';
  });

  $('#room-list').addEventListener('change', (event) => {
    if (event.target.matches('[data-compare-room]')) {
      const id = event.target.dataset.compareRoom;
      if (event.target.checked && state.compareIds.length >= 2) {
        event.target.checked = false;
        announce('You can compare 2 rooms at a time. Remove one before adding another.');
      } else if (event.target.checked) {
        state.compareIds.push(id);
      } else {
        state.compareIds = state.compareIds.filter((roomId) => roomId !== id);
      }
      updateCompareButton();
    }
    if (event.target.matches('[data-tenancy-room]')) {
      const id = event.target.dataset.tenancyRoom;
      state.tenancies[id] = Number(event.target.value);
      const room = rooms.find((item) => item.id === id);
      const row = $(`[data-room-id="${id}"]`);
      $('.room-price strong', row).textContent = formatMoney(selectedTenancy(room).weekly);
      if (id === state.selectedRoomId) updateSelectedRoom();
      announce(`Tenancy updated for ${room.name}.`);
    }
  });

  $('#room-list').addEventListener('click', (event) => {
    const button = event.target.closest('[data-select-room]');
    if (!button) return;
    state.selectedRoomId = button.dataset.selectRoom;
    updateSelectedRoom();
    $$('.room-row').forEach((row) => {
      const isSelected = row.dataset.roomId === state.selectedRoomId;
      row.classList.toggle('selected', isSelected);
      $('[data-select-room]', row).textContent = isSelected ? 'Selected room' : 'Select this room';
    });
    announce(`${selectedRoom().name} selected for enquiry.`);
  });

  $('#open-compare').addEventListener('click', () => {
    if (state.compareIds.length !== 2) {
      $('#rooms').scrollIntoView({ behavior: 'smooth', block: 'start' });
      announce('Select two rooms in the room list to compare them.');
      return;
    }
    renderComparison();
    $('#compare-dialog').showModal();
  });
}

function setSaved(saved) {
  try { localStorage.setItem('accom-iq-kingston-saved', String(saved)); } catch {}
  const control = $('#save-property');
  control.setAttribute('aria-pressed', String(saved));
  control.setAttribute('aria-label', saved ? 'Remove iQ Kingston from saved properties' : 'Save iQ Kingston');
  control.querySelector('span').textContent = saved ? 'Saved' : 'Save';

}

function setupSavedState() {
  let saved = false;
  try { saved = localStorage.getItem('accom-iq-kingston-saved') === 'true'; } catch {}
  setSaved(saved);
  const toggle = () => {
    saved = !saved;
    setSaved(saved);
    announce(saved ? 'iQ Kingston saved in this browser.' : 'iQ Kingston removed from saved properties.');
  };
  $('#save-property').addEventListener('click', toggle);

}

function setupDialogs() {
  $$('[data-close-dialog]').forEach((button) => button.addEventListener('click', () => button.closest('dialog').close()));
  $$('dialog').forEach((dialog) => dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dialog.close();
  }));
}

function openEnquiry(topic) {
  const room = selectedRoom();
  const tenancy = room ? selectedTenancy(room) : null;
  const form = $('#enquiry-form');
  form.reset();
  $('#form-state').hidden = false;
  $('#success-state').hidden = true;
  ['name', 'email', 'consent'].forEach((field) => {
    const input = form.elements.namedItem(field);
    input.removeAttribute('aria-invalid');
    input.removeAttribute('aria-describedby');
    $(`#${field}-error`).textContent = '';
  });
  $('#enquiry-room-summary').innerHTML = room
    ? `<strong>${room.name}</strong><span>${tenancy.weeks} weeks · ${formatMoney(tenancy.weekly)}/week · demo total ${formatMoney(totalRent(tenancy.weekly, tenancy.weeks))}</span>`
    : '<strong>iQ Kingston</strong><span>General property enquiry · choose a room later</span>';
  if (topic) $('#topic').value = topic;
  $('#enquiry-dialog').showModal();
  form.elements.namedItem('name').focus();
}

function setupEnquiry() {
  $$('[data-open-enquiry]').forEach((button) => button.addEventListener('click', () => openEnquiry(button.dataset.enquiryTopic)));
  $('#mobile-main-action').addEventListener('click', () => {
    if (state.selectedRoomId) openEnquiry();
    else $('#rooms').scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  $('#enquiry-form').addEventListener('submit', (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const values = readInquiryValues(form);
    const errors = validateInquiry(values);
    ['name', 'email', 'consent'].forEach((field) => {
      $(`#${field}-error`).textContent = errors[field] || '';
      const input = form.elements[field];
      input.setAttribute('aria-invalid', String(Boolean(errors[field])));
      if (errors[field]) input.setAttribute('aria-describedby', `${field}-error`); else input.removeAttribute('aria-describedby');
    });
    const firstError = Object.keys(errors)[0];
    if (firstError) {
      form.elements[firstError].focus();
      announce('Please correct the highlighted enquiry fields.');
      return;
    }
    $('#form-state').hidden = true;
    $('#success-state').hidden = false;
    const reference = `DEMO-${String(Date.now()).slice(-6)}`;
    $('#enquiry-reference').textContent = reference;
    $('#success-state').focus?.();
  });
}

function setupSectionNavigation() {
  const links = $$('.section-nav a');
  const sections = links.map((link) => $(link.getAttribute('href')));
  const update = () => {
    // The readable content area starts below the sticky glass menu. Use the
    // upper third of the viewport to keep the active pill aligned with the
    // section a student is actually reading.
    const readingLine = Math.min(window.innerHeight * .38, 300);
    let activeIndex = 0;
    for (let index = 0; index < sections.length; index++) {
      if (sections[index] && sections[index].getBoundingClientRect().top <= readingLine) {
        activeIndex = index;
      }
    }
    links.forEach((link, index) => {
      const active = index === activeIndex;
      link.classList.toggle('active', active);
      if (active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  };
  let queued = false;
  const schedule = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      update();
    });
  };
  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule, { passive: true });
  update();
}

renderRooms();
renderAccordions();
updateSelectedRoom();
setupGallery();
setupRoomInteractions();
setupSavedState();
setupDialogs();
setupEnquiry();
setupSectionNavigation();
