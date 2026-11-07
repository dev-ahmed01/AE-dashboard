
/* Dashboard-only navigation: preserve the deployed page's design and behavior. */
window.addEventListener('message',function(event){
  var msg=event.data;
  if(!msg||msg.type!=='accom-open-section')return;
  var allowed=['top','overview','about','tours','amenities','rooms','rules','payments','floorplan','neighbourhood','faqs','location','reviews'];
  if(!allowed.includes(msg.id))return;
  var section=document.getElementById(msg.id);
  if(section)section.scrollIntoView({block:'start',behavior:'instant'});
});
