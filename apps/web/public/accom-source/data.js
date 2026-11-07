/** @typedef {'provider-verified'|'dated-demo'|'illustrative'} ProvenanceKind */
/** @typedef {{ kind: ProvenanceKind, label: string, source?: string, checked?: string }} Provenance */
/** @typedef {{ weeks: number, start: string, end: string, weekly: number, availability: string }} Tenancy */
/** @typedef {{ id: string, name: string, category: 'ensuite'|'studio', image: string, area: string, privacy: string, kitchen: string, bathroom: string, inclusions: string[], tenancies: Tenancy[], provenance: Provenance }} Room */

export const property = {
  name: 'iQ Kingston',
  address: '15 Wood Street, Kingston upon Thames, KT1 1TY, United Kingdom',
  summary: 'Modern en suites and studios beside the River Thames, with social, study and wellbeing spaces in central Kingston.',
  verifiedFacts: [
    '15 min walk to Kingston University',
    '9 min walk to Kingston College',
    'Gym, cinema, games room, study spaces and roof terrace',
    'Weekly fee includes Wi-Fi, electricity and water',
  ],
  provenance: {
    kind: 'provider-verified',
    label: 'Provider information checked 26 Oct 2026',
    source: 'https://www.iqstudentaccommodation.com/kingston/iq-kingston',
    checked: '2026-10-26',
  },
};

export const media = [
  { src: '/accom-template/assets/ensuite.webp', category: 'Ensuite bedroom', alt: 'Illustrative furnished ensuite bedroom with desk and window' },
  { src: '/accom-template/assets/lounge.webp', category: 'Shared spaces', alt: 'Illustrative communal lounge with seating and study areas' },
  { src: '/accom-template/assets/studio.webp', category: 'Studio', alt: 'Illustrative private studio with kitchenette' },
  { src: '/accom-template/assets/study.webp', category: 'Study spaces', alt: 'Illustrative shared study lounge with long table and booths' },
];

/** @type {Room[]} */
export const rooms = [
  {
    id: 'bronze-ensuite',
    name: 'Bronze Ensuite',
    category: 'ensuite',
    image: '/accom-template/assets/ensuite.webp',
    area: 'Approx. 13–15 m²',
    privacy: 'Private bedroom in a shared flat',
    kitchen: 'Shared kitchen & living space',
    bathroom: 'Private shower room',
    inclusions: ['Small double bed', 'Study desk', 'Storage', 'All-inclusive bills'],
    tenancies: [
      { weeks: 51, start: '12 Sep 2027', end: '3 Sep 2028', weekly: 289, availability: 'Request availability' },
      { weeks: 44, start: '12 Sep 2027', end: '16 Jul 2028', weekly: 305, availability: 'Request availability' },
    ],
    provenance: { kind: 'dated-demo', label: 'Illustrative price & dates for prototype comparison — not live availability', checked: '2026-10-26' },
  },
  {
    id: 'silver-ensuite',
    name: 'Silver Ensuite',
    category: 'ensuite',
    image: '/accom-template/assets/ensuite.webp',
    area: 'Approx. 15–17 m²',
    privacy: 'Private bedroom in a shared flat',
    kitchen: 'Shared kitchen & living space',
    bathroom: 'Private shower room',
    inclusions: ['Small double bed', 'Larger floor area', 'Study desk', 'All-inclusive bills'],
    tenancies: [
      { weeks: 51, start: '12 Sep 2027', end: '3 Sep 2028', weekly: 315, availability: 'Request availability' },
      { weeks: 44, start: '12 Sep 2027', end: '16 Jul 2028', weekly: 329, availability: 'Request availability' },
    ],
    provenance: { kind: 'dated-demo', label: 'Illustrative price & dates for prototype comparison — not live availability', checked: '2026-10-26' },
  },
  {
    id: 'bronze-studio',
    name: 'Bronze Studio',
    category: 'studio',
    image: '/accom-template/assets/studio.webp',
    area: 'Approx. 18–20 m²',
    privacy: 'Self-contained private room',
    kitchen: 'Private kitchenette',
    bathroom: 'Private shower room',
    inclusions: ['Double bed', 'Private kitchenette', 'Study desk', 'All-inclusive bills'],
    tenancies: [
      { weeks: 51, start: '12 Sep 2027', end: '3 Sep 2028', weekly: 365, availability: 'Request availability' },
      { weeks: 44, start: '12 Sep 2027', end: '16 Jul 2028', weekly: 389, availability: 'Request availability' },
    ],
    provenance: { kind: 'dated-demo', label: 'Illustrative price & dates for prototype comparison — not live availability', checked: '2026-10-26' },
  },
];

export const policies = [
  { title: 'Cancellation & visa conditions', body: 'Property-specific cancellation and visa terms were not available in a stable source for this prototype. Ask an Accom adviser for the current iQ terms before paying or signing.' },
  { title: 'Booking fee & deposits', body: 'iQ states that its site-specific booking fee secures a room, is credited to the first rent instalment and is generally non-refundable except in limited circumstances. The exact iQ Kingston amount must be confirmed.' },
  { title: 'Payments & guarantors', body: 'Payment schedule, instalment options and guarantor requirements vary by contract. Your Accom enquiry does not create a contract or take a payment.' },
  { title: 'Accessibility', body: 'Step-free routes, lift dimensions and accessible-room specifications have not been verified for this prototype. Use the accessibility enquiry option so the operator can confirm the exact route and room.' },
];

export const faqs = [
  ['Are bills included?', 'The operator says weekly rent includes Wi-Fi, electricity and water. Laundry machines are operated by a third party and are paid separately. Confirm heating and any usage terms for your chosen contract.'],
  ['What is the difference between an ensuite and a studio?', 'An ensuite has a private bedroom and bathroom with a shared kitchen. A studio adds a private kitchenette and is self-contained.'],
  ['Can I choose an exact room?', 'iQ says students can choose from available rooms on its floor plan after selecting a room type and contract. An Accom enquiry asks for help; it does not reserve an exact room.'],
  ['Can visitors stay?', 'Visitor and overnight guest rules were not verified for this prototype. Ask for the current house rules before you proceed.'],
  ['How secure is the building?', 'iQ describes 24/7 security and staff presence across its accommodation. Ask the operator to confirm the access-control and reception arrangements at iQ Kingston.'],
  ['What happens after I enquire?', 'This prototype shows a demonstration confirmation only and sends no message. In a live Accom service, an adviser would confirm the options and next steps. A booking is only confirmed by the accommodation provider.'],
  ['Can I cancel?', 'Cancellation depends on the current provider contract and your circumstances. Request the full policy before paying or signing.'],
  ['When can I move in?', 'The dates shown here are illustrative prototype values. Current move-in dates must be confirmed with iQ.'],
];

export const formatMoney = (value) => new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP', maximumFractionDigits: 0 }).format(value);
export const totalRent = (weekly, weeks) => weekly * weeks;
export const filterRooms = (list, category) => category === 'all' ? list : list.filter((room) => room.category === category);

// Resolve form controls by name through the elements collection. form.name is the
// HTMLFormElement's own name property, not a reliable reference to the input.
export function readInquiryValues(form) {
  const control = (name) => form.elements.namedItem(name);
  return {
    name: control('name')?.value ?? '',
    email: control('email')?.value ?? '',
    phone: control('phone')?.value ?? '',
    consent: Boolean(control('consent')?.checked),
  };
}

export function validateInquiry(values) {
  const errors = {};
  if (!values.name?.trim()) errors.name = 'Enter your name.';
  if (!/^\S+@\S+\.\S+$/.test(values.email || '')) errors.email = 'Enter an email address in the format name@example.com.';
  if (!values.consent) errors.consent = 'Confirm that Accom may contact you about this enquiry.';
  return errors;
}
