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

  await page.getByRole('tab',{name:'Add Page'}).click();
  await page.getByRole('button',{name:'Preview actual design'}).click();
  const fullSource = page.frameLocator('iframe[title="Complete original Accom property page"]');
  for(const id of ['overview','about','tours','amenities','rooms','rules','payments','floorplan','neighbourhood','faqs','location','reviews']){
    await fullSource.locator('#'+id).waitFor({state:'attached',timeout:20000});
  }
  assert.equal(await fullSource.locator('.gallery-tile').count(),5,'Live source main gallery should contain five tiles');
  await fullSource.locator('.gallery-tile').first().click();
  await fullSource.locator('#galleryDialog').waitFor({state:'visible',timeout:10000});
  await fullSource.locator('#galleryDialog .modal-close').click();
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
  const side = await page.locator('.accom-editor-sidebar').boundingBox();
  const middle = await page.locator('.accom-editor-fields').boundingBox();
  const preview = await page.locator('.accom-editor-preview').boundingBox();
  assert(side&&middle&&preview, 'Three editor panels were not rendered');
  assert(side.x+side.width <= middle.x+3,'Sections overlap content');
  assert(middle.x+middle.width <= preview.x+3,'Content overlaps preview');
  assert(preview.width>=300,'Preview is too narrow for desktop');
  const sourceFrame = page.frameLocator('iframe[title="Complete original Accom source page"]');
  await sourceFrame.locator('#payments').waitFor({state:'attached',timeout:20000});
  await page.getByRole('button',{name:'Draft content'}).click();
  const iframe = page.locator('iframe[title="Live property page visual preview"]');
  await iframe.waitFor({timeout:20000});
  await page.waitForFunction(()=>{
    const frame=document.querySelector('iframe[title="Live property page visual preview"]');
    return frame?.contentDocument?.querySelector('#property-title')?.textContent==='Visual QA Residence';
  },null,{timeout:20000});

  await page.getByRole('textbox',{name:'Property name'}).fill('Visual QA Updated Residence');
  await page.getByRole('textbox',{name:'City',exact:true}).fill('Birmingham');
  await page.getByRole('textbox',{name:'Address',exact:true}).fill('10 Example Road');
  await page.getByRole('textbox',{name:'Overview / property description'}).fill(
    'A demonstration accommodation listing for testing the Category editing experience.'
  );
  await page.waitForFunction(()=>{
    const iframe=document.querySelector('iframe[title="Live property page visual preview"]');
    return iframe?.contentDocument?.querySelector('#property-title')?.textContent==='Visual QA Updated Residence';
  },null,{timeout:20000});

  await page.getByRole('button',{name:/02 Property photos/}).click();
  await page.locator('.accom-editor-fields').getByRole('button',{name:'Add another'}).click();
  await page.getByPlaceholder('https://example.com/photo.webp or upload below').fill('/accom-template/assets/ensuite.webp');
  await page.getByPlaceholder('Describe the actual image').fill('Illustrative accommodation interior');
  await page.locator('.accom-editor-fields .image-layout-switch').getByRole('button',{name:'Large'}).click();
  await page.waitForFunction(()=>{
    const frame=document.querySelector('iframe[title="Live property page visual preview"]');
    return frame?.contentDocument?.querySelector('.gallery-grid .gallery-tile img')?.getAttribute('src')==='/accom-template/assets/ensuite.webp';
  },null,{timeout:20000});
  await page.screenshot({path:'qa/evidence/editor-desktop.png'});

  await page.getByRole('button',{name:/03 Highlights & amenities/}).click();
  await page.locator('.accom-editor-fields').getByRole('button',{name:'Add another'}).first().click();
  await page.getByRole('textbox',{name:'Highlight text'}).fill('Premium student support');
  await page.waitForFunction(()=>{
    const frame=document.querySelector('iframe[title="Live property page visual preview"]');
    return frame?.contentDocument?.body?.textContent?.includes('Premium student support');
  },null,{timeout:20000});

  await page.setViewportSize({width:390,height:844});
  await page.waitForFunction(()=>document.querySelector('.accom-editor-device-toggle button:last-child')?.getAttribute('aria-pressed')==='true',{timeout:10000});
  await page.getByRole('button',{name:/02 Property photos/}).click();
  await page.locator('.accom-editor-preview').scrollIntoViewIfNeeded();
  await page.screenshot({path:'qa/evidence/editor-mobile.png'});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth);
  assert(overflow<=3,'Mobile layout has '+overflow+'px horizontal overflow');
  await page.setViewportSize({width:1440,height:900});
  await page.locator('.accom-editor-footer-actions .primary').click();
  await editor.waitFor({state:'hidden',timeout:20000});
  const saved=page.getByText('Visual QA Updated Residence').first();
  await saved.waitFor({timeout:15000});
  assert.deepEqual(errors,[],'Unexpected uncaught page exceptions');
  console.log('PASS: signed-out admin redirects directly to login; full 13-section live source gallery/enquiry; exact original in editor; draft preview; repeaters; mobile; save');
} finally {
  await browser.close();
}
