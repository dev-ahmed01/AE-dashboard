import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';

const base = 'http://127.0.0.1:5173';
await mkdir('qa/evidence',{recursive:true});
const browser = await chromium.launch({headless:true});
const page = await browser.newPage({viewport:{width:1440,height:900},deviceScaleFactor:1});
const errors = [];
page.on('pageerror', err => errors.push(err.message));

try {
  const guest = await browser.newPage();
  await guest.goto(base+'/admin',{waitUntil:'domcontentloaded'});
  await guest.waitForURL('**/login',{timeout:15000});
  assert(await guest.getByText('Good to have you back.').isVisible(),'Admin must go straight to login');
  await guest.close();
  await page.goto(base+'/login',{waitUntil:'domcontentloaded'});
  await page.getByLabel('Email or username').fill('Admin');
  await page.locator('.auth-form input[type=password]').fill('Admin@123');
  await page.locator('.auth-form button.primary').click();
  await page.waitForURL('**/admin',{timeout:30000});

  await page.getByRole('tab',{name:'All Pages'}).click();
  assert(await page.getByRole('tab',{name:'Add Page'}).isVisible());
  assert(await page.getByRole('tab',{name:'Upload Template'}).isVisible());
  assert.equal(await page.locator('.category-table-header').count(),1,'Minimal directory table must exist');
  assert.equal(await page.getByText('iQ Kingston',{exact:true}).count(),0,'Old seeded demo should not appear in page directory');
  await page.getByRole('tab',{name:'Add Page'}).click();
  const addPreview=page.frameLocator('iframe[title="Approved Accom template preview"]');
  await addPreview.locator('#payments').waitFor({state:'attached',timeout:20000});
  await page.screenshot({path:'qa/evidence/category-add-page.png'});
  await page.getByRole('button',{name:/Expand/}).click();
  const fullSource = page.frameLocator('iframe[title="Complete original Accom property page"]');
  for(const id of ['overview','about','tours','amenities','rooms','rules','payments','floorplan','neighbourhood','faqs','location','reviews']){
    await fullSource.locator('#'+id).waitFor({state:'attached',timeout:20000});
  }
  assert.equal(await fullSource.locator('.gallery-tile').count(),5,'Live source main gallery should contain five tiles');
  await page.screenshot({path:'qa/evidence/exact-original-source-in-category.png'});
  await fullSource.locator('.gallery-tile').first().click();
  await fullSource.locator('#galleryDialog').waitFor({state:'visible',timeout:10000});
  await fullSource.locator('#galleryDialog [aria-label="Close photo tour"]').click();
  await fullSource.locator('#galleryDialog').waitFor({state:'hidden',timeout:10000});
  await fullSource.locator('[data-enquire]').first().click();
  await fullSource.locator('#enquiryDialog').waitFor({state:'visible',timeout:10000});
  await fullSource.locator('#enquiryDialog .modal-close').click();
  await page.getByRole('button',{name:/Back to Category/}).click();
  const name = page.getByRole('textbox',{name:'Page name'});
  await name.waitFor();
  const width = await name.evaluate(el=>el.getBoundingClientRect().width);
  assert(width>=350,'Add Page name input is too narrow: '+width);
  await name.fill('Visual QA Residence');
  await page.getByRole('button',{name:'Create page'}).click();
  const editor = page.locator('.accom-page-editor');
  await editor.waitFor({state:'visible',timeout:20000});
  const appSidebar=await page.locator('.accom-editor-site-sidebar').boundingBox();
  const stacked=await page.locator('.accom-stacked-sections').boundingBox();
  const preview = await page.locator('.accom-editor-preview').boundingBox();
  assert(appSidebar&&stacked&&preview, 'Global brand sidebar, stacked forms and preview must render');
  assert(appSidebar.width>=195&&stacked.x>=appSidebar.x+appSidebar.width,'Keep the original global brand sidebar');
  assert.equal(await page.locator('.accom-editor-sidebar').count(),0,'Remove the extra Edit sections sidebar entirely');
  assert(stacked.x+stacked.width <= preview.x+3,'Stacked forms must not overlap preview');
  assert.equal(await page.locator('.accom-stack-section').count(),15,'All fifteen property sections must be visible in page order');
  assert.equal(await page.locator('.accom-editor-right-panel').count(),1,'Preview, SEO, and Static must share the right-hand panel');
  assert.equal(await page.locator('.accom-editor-seo-section').count(),0,'No duplicated full-width SEO area');
  assert(preview.width>=300,'Preview is too narrow for desktop');
  assert(preview.height>=440,'Preview must be tall enough to inspect page details');
  assert(await page.locator('.accom-editor-topbar').isVisible(),'Breadcrumb top bar should match Workspace dashboard');
  assert(await page.locator('.accom-editor-head-actions .primary').isVisible(),'Save draft should appear in the page header');
  const iframe = page.locator('iframe[title="Live property page visual preview"]');
  await page.screenshot({path:'qa/evidence/editor-we-layout.png'});
  await iframe.waitFor({timeout:20000});
  await page.waitForFunction(()=>{
    const frame=document.querySelector('iframe[title="Live property page visual preview"]');
    return frame?.contentDocument?.querySelector('.property-heading h1')?.textContent==='Visual QA Residence';
  },null,{timeout:20000});
  const originalSections=['overview','about','tours','amenities','rooms','rules','payments','floorplan','neighbourhood','faqs','location','reviews'];
  for(const id of originalSections){
    await page.frameLocator('iframe[title="Live property page visual preview"]').locator('#'+id).waitFor({state:'attached'});
  }
  assert.equal(await page.frameLocator('iframe[title="Live property page visual preview"]').locator('style').count()>0,true,
    'Draft preview must retain original inline styling');
  assert.equal(await page.frameLocator('iframe[title="Live property page visual preview"]').locator('script[src="/accom-template/original-master.js"]').count(),1,
    'Draft preview must run the actual original page script');
  assert.equal(await page.frameLocator('iframe[title="Live property page visual preview"]').locator('#railPrice').count(),1,
    'Original sticky pricing sidebar must be intact');
  assert.equal(await page.frameLocator('iframe[title="Live property page visual preview"]').locator('.gallery-tile').count(),5,
    'Unfilled admin preview displays original sample gallery, explicitly labeled as a template example');
  const previewStart = await page.frameLocator('iframe[title="Live property page visual preview"]').locator('body').evaluate(()=>window.scrollY);
  assert(previewStart<=20,'New property draft must open at original hero/gallery, not skip straight to a lower section: '+previewStart);
  await page.screenshot({path:'qa/evidence/exact-master-draft-preview-loaded.png'});
  const draftFrame = page.frameLocator('iframe[title="Live property page visual preview"]');
  await draftFrame.locator('.gallery-tile').first().click();
  await draftFrame.locator('#galleryDialog').waitFor({state:'visible',timeout:10000});
  await draftFrame.locator('#galleryDialog [aria-label="Close photo tour"]').click();
  await draftFrame.locator('#galleryDialog').waitFor({state:'hidden',timeout:10000});


  await page.locator('.accom-editor-preview-controls').getByRole('button',{name:'Original',exact:true}).click();
  const sourceFrame=page.frameLocator('iframe[title="Complete original Accom source page"]');
  await sourceFrame.locator('#payments').waitFor({state:'attached',timeout:20000});
  await page.locator('.accom-editor-preview-controls').getByRole('button',{name:'Draft',exact:true}).click();
  await page.getByRole('textbox',{name:'Property name'}).fill('Visual QA Updated Residence');
  await page.getByRole('textbox',{name:'City',exact:true}).fill('Birmingham');
  await page.getByRole('textbox',{name:'Address',exact:true}).fill('10 Example Road');
  await page.getByRole('button',{name:/Residence overview/}).click();
  await page.getByRole('textbox',{name:'Overview / property description'}).fill(
    'A demonstration accommodation listing for testing the Category editing experience.'
  );
  await page.waitForFunction(()=>{
    const iframe=document.querySelector('iframe[title="Live property page visual preview"]');
    return iframe?.contentDocument?.querySelector('.property-heading h1')?.textContent==='Visual QA Updated Residence';
  },null,{timeout:20000});

  await page.getByRole('button',{name:/Photo gallery/}).click();
  await page.locator('.accom-stack-expanded').getByRole('button',{name:'Add another'}).click();
  await page.getByPlaceholder('https://example.com/photo.webp or upload below').fill('/accom-template/assets/ensuite.webp');
  await page.getByPlaceholder('Describe the actual image').fill('Illustrative accommodation interior');
  await page.locator('.accom-stack-expanded .image-layout-switch').getByRole('button',{name:'Large'}).click();
  await page.waitForFunction(()=>{
    const frame=document.querySelector('iframe[title="Live property page visual preview"]');
    return frame?.contentDocument?.querySelector('section.gallery > .gallery-tile img')?.getAttribute('src')==='/accom-template/assets/ensuite.webp';
  },null,{timeout:20000});
  await page.screenshot({path:'qa/evidence/editor-desktop.png'});

  await page.getByRole('button',{name:/Residence overview/}).click();
  await page.locator('.accom-stack-expanded').getByRole('button',{name:'Add another'}).first().click();
  await page.getByRole('textbox',{name:'Highlight title',exact:true}).fill('Premium student support');
  await page.waitForFunction(()=>{
    const frame=document.querySelector('iframe[title="Live property page visual preview"]');
    return frame?.contentDocument?.body?.textContent?.includes('Premium student support');
  },null,{timeout:20000});

  assert.equal(await page.locator('.accom-stack-section').count(),15,
    'Editor navigation must reflect all fifteen editable property areas');
  await page.getByRole('button',{name:/Living experience/}).click();
  await page.locator('.accom-copy-field').first().waitFor({state:'visible',timeout:15000});
  const actualCopy = await page.locator('.accom-copy-field input,.accom-copy-field textarea').first().inputValue();
  assert(actualCopy.trim().length>1,'Mapped page fields must be prefilled from the rendered design');
  const storyHeading = page.locator('.accom-copy-panel').getByRole('textbox',{name:'Section heading'}).first();
  await storyHeading.fill('Designed around your student life');
  await page.waitForFunction(()=>{
    const frame=document.querySelector('iframe[title="Live property page visual preview"]');
    return frame?.contentDocument?.querySelector('#about h2')?.textContent?.includes('Designed around your student life');
  },null,{timeout:20000});
  await page.screenshot({path:'qa/evidence/prefilled-page-copy-edit.png'});
  await page.getByRole('button',{name:'SEO settings',exact:true}).click();
  assert(await page.getByRole('tab',{name:'SEO'}).getAttribute('aria-selected')==='true','SEO tab opens on right');
  const seoPanel=page.locator('.accom-right-seo');
  await seoPanel.getByRole('textbox',{name:/SEO title/}).fill('Campus ready student accommodation');
  await seoPanel.getByRole('textbox',{name:/Meta description/}).fill('Find genuine accommodation details and clear pricing.');
  await seoPanel.getByRole('textbox',{name:/Canonical URL/}).fill('https://example.org/student-living/test');
  await seoPanel.getByRole('checkbox',{name:'No Index'}).check();
  assert(await seoPanel.getByRole('checkbox',{name:'Index',exact:true}).isChecked()===false,'Index and No Index are exclusive');
  await seoPanel.getByRole('checkbox',{name:'Index',exact:true}).check();
  await seoPanel.getByRole('checkbox',{name:'Nofollow'}).check();
  await seoPanel.getByRole('checkbox',{name:'No Archive'}).check();
  await seoPanel.getByRole('checkbox',{name:'No Image Index'}).check();
  await seoPanel.getByRole('checkbox',{name:'No Snippet'}).check();
  assert.equal(await page.locator('.accom-editor-right-panel').count(),1,'SEO stays on right');
  assert.equal(await page.locator('.accom-editor-workspace input[placeholder*="slug"]').count(),0,'URL slug removed from the editor');
  await page.screenshot({path:'qa/evidence/seo-right-panel.png'});

  await page.getByRole('tab',{name:'Static'}).click();
  const staticPanel=page.locator('.accom-right-static');
  assert.equal(await staticPanel.locator('.accom-static-row').count(),15,'Static tab shows all page sections');
  await staticPanel.getByRole('checkbox',{name:'Static Payments & fees'}).check();
  const staticRow=staticPanel.locator('.accom-static-row').filter({has:staticPanel.getByRole('checkbox',{name:'Static Payments & fees'})});
  const staticRowLayout=await staticRow.evaluate(el=>{
    const label=el.querySelector('span:first-child').getBoundingClientRect();
    const track=el.querySelector('.accom-static-switch').getBoundingClientRect();
    return {labelRight:label.right,trackLeft:track.left,labelTop:label.top,trackTop:track.top,trackBottom:track.bottom,labelBottom:label.bottom};
  });
  assert(staticRowLayout.trackLeft>=staticRowLayout.labelRight-4,
    'Static switches should align to the right of row text: '+JSON.stringify(staticRowLayout));
  await page.getByRole('button',{name:/Payments & fees/}).click();
  assert((await page.locator('#accom-section-payments fieldset').getAttribute('disabled'))!==null,'Static sections must apply the native disabled fieldset attribute');
  assert(await page.locator('#accom-section-payments fieldset button').first().isDisabled(),'Locked section action buttons must be disabled');
  await page.screenshot({path:'qa/evidence/static-right-panel.png'});
  await page.getByRole('tab',{name:'Preview'}).click();
  assert(await page.locator('iframe[title="Live property page visual preview"]').count()===1,'Preview remains accessible after SEO and Static');
  await page.getByRole('button',{name:/Property identity/}).click();
  assert.equal(await page.locator('.accom-stack-section').count(),15);

  await page.setViewportSize({width:390,height:844});
  await page.waitForFunction(()=>document.querySelector('.accom-editor-device-toggle button:last-child')?.getAttribute('aria-pressed')==='true',{timeout:10000});
  await page.getByRole('button',{name:/Photo gallery/}).click();
  await page.locator('.accom-editor-preview').scrollIntoViewIfNeeded();
  await page.screenshot({path:'qa/evidence/editor-mobile.png'});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth);
  assert(overflow<=3,'Mobile layout has '+overflow+'px horizontal overflow');
  await page.setViewportSize({width:1440,height:900});
  await page.locator('.accom-editor-head-actions .primary').click();
  await editor.waitFor({state:'hidden',timeout:20000});
  const saved=page.getByText('Visual QA Updated Residence').first();
  await saved.waitFor({timeout:15000});
  await page.screenshot({path:'qa/evidence/category-pages-desktop.png'});
  // A brand-new demo draft must open with real, editable examples from
  // the approved master — not empty city, address, highlights or photos.
  await page.getByRole('tab',{name:'Add Page'}).click();
  await page.getByRole('textbox',{name:'Page name'}).fill('Demo_11');
  await page.getByRole('button',{name:'Create page'}).click();
  await editor.waitFor({state:'visible',timeout:20000});
  await page.locator('.accom-template-sample-note').waitFor({state:'visible',timeout:20000});
  assert.equal(await page.getByRole('textbox',{name:'City',exact:true}).inputValue(),
    'Kingston upon Thames','The inspected original city must fill the demo field');
  assert.equal(await page.getByRole('textbox',{name:'Address',exact:true}).inputValue(),
    '15 Wood Street','The inspected original address must fill the demo field');
  assert.equal(await page.getByRole('textbox',{name:'Postcode',exact:true}).inputValue(),'KT1 1TY');
  assert.equal(await page.locator('.accom-stack-section').count(),15);
  await page.waitForFunction(()=>{
    const frame=document.querySelector('iframe[title="Live property page visual preview"]');
    const doc=frame?.contentDocument;
    return doc?.querySelector('.property-address')?.textContent?.includes('15 Wood Street') &&
      doc?.querySelector('#overview .intro-text')?.textContent?.includes('Modern en suite rooms');
  },null,{timeout:25000});
  assert.equal(await page.frameLocator('iframe[title="Live property page visual preview"]').locator('section.gallery > .gallery-tile').count(),4,
    'Preview must render the supplied, unverified gallery photos in the original layout');
  await page.screenshot({path:'qa/evidence/demo-identity-prefilled.png'});
  await page.getByRole('button',{name:/Photo gallery/}).click();
  assert.equal(await page.locator('.accom-stack-expanded .repeater-group .repeater-item').count(),4,
    'Four illustrative master photos must be ready to edit');
  await page.screenshot({path:'qa/evidence/demo-gallery-prefilled.png'});
  await page.getByRole('button',{name:/Residence overview/}).click();
  assert((await page.getByRole('textbox',{name:'Overview / property description'}).inputValue()).length>40,
    'Overview must be prefilled with original page text');
  await page.screenshot({path:'qa/evidence/demo-overview-prefilled.png'});
  await page.locator('.accom-editor-head-actions .primary').click();
  await editor.waitFor({state:'hidden',timeout:20000});
  // Creating a draft with illustrative values must never publish it.
  await page.getByText('Demo_11',{exact:true}).first().waitFor({timeout:15000});
  await page.getByRole('tab',{name:'Upload Template'}).click();
  await page.locator('.category-upload-drop input[type=file]').setInputFiles({
    name:'Listing.tsx',mimeType:'text/plain',
    buffer:Buffer.from('export default function Listing(){return <main><h1>Student living in Kingston</h1><button>Request a viewing</button><img src="/room.webp" /></main>}')
  });
  await page.getByRole('button',{name:/Inspect project/}).click();
  const inspection=page.locator('.category-project-results');
  await inspection.waitFor({state:'visible',timeout:15000});
  assert(await inspection.getByText('Student living in Kingston').count()>0,'Source heading must be detected');
  assert(await inspection.getByText('Build/export required for visual editing.').isVisible(),'Dynamic component cannot be represented as pixel-perfect HTML without build');
  await page.screenshot({path:'qa/evidence/category-source-inspection.png'});
  assert.deepEqual(errors,[],'Unexpected uncaught page exceptions');
  console.log('PASS: stacked sections with right Preview/SEO/Static tabs, robots options, lock fields, saved draft, mobile and project inspection');
} finally {
  await browser.close();
}
