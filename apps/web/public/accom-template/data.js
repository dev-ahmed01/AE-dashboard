/* Native Accom property template data adapter.
   Readonly listing data injected by the server. No demo constants. */
const root=document.getElementById('accom-property-data');
export const snapshot=root?JSON.parse(root.textContent||'{}'):{};
export const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
}[c]));
const validImage=url=>/^https:\/\//.test(url||'')||
  /^\/(?:api\/media\/\d+|accom-template\/assets\/[a-z0-9_-]+\.(?:webp|jpg|png))$/.test(url||'');
export const property={
  name:esc(snapshot.name||'Accommodation'),
  address:esc([snapshot.address,snapshot.postcode,snapshot.city].filter(Boolean).join(', ')),
  summary:esc(snapshot.description||''),
  verifiedFacts:(snapshot.highlights||[]).map(esc)
};
export const media=(snapshot.gallery||[]).filter(img=>validImage(img.url)).map(img=>({
  src:img.url,alt:esc(img.alt||'Property photo'),
  category:esc(img.category||'Property photo'),
  layout:img.layout==='large'?'large':'regular'
}));
export const rooms=(snapshot.rooms||[]).filter(room=>room.active&&room.availability!=='unavailable').map(room=>({
 id:String(room.id),name:esc(room.name),
 category:/studio/i.test(room.room_type)?'studio':'ensuite',
 image:validImage(room.image_url)?room.image_url:(media[0]?.src||''),
 area:esc(room.size_sqm?('Approx. '+room.size_sqm+' m²'):'Size to confirm'),
 privacy:esc(room.details||'Specifications to confirm'),
 bathroom:esc(room.bathroom||'Confirm with provider'),
 kitchen:esc(room.kitchen||'Confirm with provider'),
 inclusions:(snapshot.amenities||[]).slice(0,4).map(esc),
 tenancies:((room.tenancies&&room.tenancies.length)?room.tenancies:[{
    weeks:0,start:'Dates to confirm',end:'',weekly:room.price,
    availability:'Request availability',illustrative:false
 }]).map(t=>({
    weeks:Number(t.weeks)||0,start:esc(t.start||'Dates to confirm'),
    end:esc(t.end||''),weekly:t.weekly==null?null:Number(t.weekly),
    availability:esc(t.availability||'Request availability'),
    illustrative:Boolean(t.illustrative)
 })),
 provenance:{kind:snapshot.is_demo?'dated-demo':'provider-verified',
   label:snapshot.is_demo?'Illustrative tenancy prices — not live availability':
        'Verify current rates and provider terms before booking'}
}));
export const policies=(snapshot.policies||[]).map(x=>({title:esc(x.question),body:esc(x.answer)}));
export const faqs=(snapshot.faq||[]).map(x=>[esc(x.question),esc(x.answer)]);
export const formatMoney=value=>value==null||!Number.isFinite(Number(value))||Number(value)<=0
 ?'Price on request'
 :new Intl.NumberFormat('en-GB',{style:'currency',currency:'GBP',maximumFractionDigits:0}).format(value);
export const totalRent=(weekly,weeks)=>weekly&&weeks?Number(weekly)*Number(weeks):null;
export const filterRooms=(all,category)=>category==='all'?all:all.filter(x=>x.category===category);
export function readInquiryValues(form){
 const c=name=>form.elements.namedItem(name);
 return {name:c('name')?.value??'',email:c('email')?.value??'',
         phone:c('phone')?.value??'',consent:Boolean(c('consent')?.checked)};
}
export function validateInquiry(v){
 const errors={};
 if(!v.name?.trim())errors.name='Enter your name.';
 if(!/^\S+@\S+\.\S+$/.test(v.email||''))errors.email='Enter an email address in the format name@example.com.';
 if(!v.consent)errors.consent='Confirm that Accom may contact you about this enquiry.';
 return errors;
}
