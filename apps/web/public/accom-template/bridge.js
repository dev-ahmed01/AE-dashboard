/* Safe bridge from the approved property design to Accom API.
   Uploaded third-party HTML remains isolated and cannot execute this script. */
import {snapshot,media,property,readInquiryValues,validateInquiry} from './data.js';
const $=q=>document.querySelector(q), all=q=>[...document.querySelectorAll(q)];
const put=(q,value)=>{const el=$(q);if(el)el.textContent=String(value??'')};
const storedToken=sessionStorage.getItem('accom_token')||'';
function hydrate(){
 const address=[snapshot.address,snapshot.postcode,snapshot.city].filter(Boolean).join(', ');
 put('#property-title',snapshot.name);
 put('.address',address);
 put('.cta-property-title h2',snapshot.name);
 put('.cta-address',address);
 put('.cta-kicker','STUDENT LIVING · '+(snapshot.city||'UK').toUpperCase());
 put('#overview .overview-lead',snapshot.description);
 put('.cta-price-hero small',snapshot.is_demo?'Illustrative from':'Rooms from');
 put('.cta-footnote',snapshot.is_demo?
   'Demo prices and illustrative media. No live booking or verified availability.':
   'Rates and availability require confirmation. Payments go directly to the operator.');
 put('.site-footer .footer-meta',snapshot.is_demo?
   'Property-detail demonstration · no live booking':
   'Accommodation advice and enquiries · no rent collection');
 const note=$('.overview-footnote');if(note)note.textContent=snapshot.is_demo?
   'Illustrative room images and prices, not current provider availability.':
   'Confirm the final contract and property-specific policies before paying.';
 const label=$('.verified-copy');if(label)label.textContent=snapshot.is_demo?'Demo details':'Details to confirm';
 const save=$('#save-property');if(save)save.setAttribute('aria-label','Save '+snapshot.name);
 const facts=all('.overview-card .fact-pill,.overview-card .feature-pill');
 facts.forEach((el,i)=>{if(i<property.verifiedFacts.length)el.textContent=property.verifiedFacts[i];else el.hidden=true});
 const thumbs=all('.gallery-tile');
 media.forEach((photo,i)=>{
   const btn=thumbs[i],img=btn?.querySelector('img');
   if(img){img.src=photo.src;img.alt=photo.alt;}
   if(btn){btn.dataset.galleryIndex=String(i);btn.classList.toggle('gallery-main',photo.layout==='large')}
 });
 thumbs.slice(media.length).forEach(btn=>{btn.hidden=true;btn.style.display='none'});
 const gallery=$('.gallery-grid');if(gallery&&media.length===1)gallery.classList.add('single-photo');
 const map=$('.cta-google-map'),locationText=[snapshot.address,snapshot.city,snapshot.postcode].filter(Boolean).join(' ');
 if(map){map.src='https://maps.google.com/maps?q='+encodeURIComponent(locationText)+'&z=16&output=embed';map.title='Map for '+snapshot.name}
 put('.cta-google-map-place strong',snapshot.name);
 put('.cta-google-map-place small',[snapshot.address,snapshot.postcode].filter(Boolean).join(', '));
 const mapLink=$('.cta-google-map-caption a');
 if(mapLink)mapLink.href='https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(locationText);
 const modalText=$('#enquiry-dialog .enquiry-visual p');
 if(modalText)modalText.textContent='Ask Accom to confirm room availability and contract terms. An enquiry is not a booking.';
 put('#success-state h3','Enquiry received');
 put('#success-state p','Your request has been recorded for the Accom team. No room is reserved or booked.');
 put('#success-state dt','Enquiry reference');
 if(snapshot.preview){
   const button=$('#enquiry-form .submit-enquiry');
   if(button)button.textContent='Test enquiry (preview only)';
 }
}
document.addEventListener('submit',async ev=>{
 const form=ev.target;if(form?.id!=='enquiry-form')return;
 ev.preventDefault();ev.stopImmediatePropagation();
 const values=readInquiryValues(form),errors=validateInquiry(values);
 for(const key of ['name','email','consent']){
   const node=$('#'+key+'-error');if(node)node.textContent=errors[key]||'';
 }
 if(Object.keys(errors).length){form.elements.namedItem(Object.keys(errors)[0])?.focus();return}
 const button=$('.submit-enquiry');if(button)button.disabled=true;
 try{
  if(snapshot.preview){
    put('#enquiry-reference','PREVIEW - NOT SENT');
    put('#success-state h3','Test successful — no enquiry sent');
  }else{
    const row=$('.room-row.selected'),roomId=row?Number(row.dataset.roomId):null;
    const response=await fetch('/api/enquiries',{method:'POST',headers:{
      'Content-Type':'application/json',...(storedToken?{Authorization:'Bearer '+storedToken}:{})
    },body:JSON.stringify({property_id:snapshot.id,room_id:roomId,
        name:values.name,email:values.email,phone:values.phone,
        message:form.elements.namedItem('message')?.value||'',
        consent:values.consent})});
    const result=await response.json();
    if(!response.ok)throw new Error(typeof result.detail==='string'?result.detail:'Could not send enquiry');
    put('#enquiry-reference','ACCOM-'+result.id);
    put('#success-state h3','Enquiry received');
  }
  $('#form-state').hidden=true;$('#success-state').hidden=false;
  $('#success-state').focus();
 }catch(error){
  const el=$('#consent-error');if(el)el.textContent=error.message||'Please try again.';
 }finally{if(button)button.disabled=false}
},true);
document.addEventListener('click',async ev=>{
 const btn=ev.target.closest?.('#save-property');if(!btn)return;
 ev.preventDefault();ev.stopImmediatePropagation();
 if(snapshot.preview)return;
 if(!storedToken){location.assign('/login');return}
 try{
  const response=await fetch('/api/me/saved/'+snapshot.id,{method:'POST',
    headers:{Authorization:'Bearer '+storedToken}});
  if(!response.ok)throw new Error('Sign in with a student account to save this property');
  btn.setAttribute('aria-pressed','true');
  const label=btn.querySelector('span');if(label)label.textContent='Saved';
 }catch(error){alert(error.message)}
},true);
hydrate();
