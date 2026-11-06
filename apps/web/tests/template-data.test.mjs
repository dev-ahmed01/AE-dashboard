import test from 'node:test'
import assert from 'node:assert/strict'

const fake={
 id:9,name:'Test <script>alert(1)</script> Residence',city:'Kingston',
 address:'Street 5',description:'A simple sample property',is_demo:true,
 gallery:[
  {url:'/accom-template/assets/ensuite.webp',alt:'Bedroom',layout:'large'},
  {url:'javascript:alert(1)',alt:'Untrusted'}
 ],
 amenities:['Wi-Fi','Study space'],faq:[{question:'How much?',answer:'Ask the team.'}],
 policies:[{question:'Terms',answer:'Confirm terms.'}],
 rooms:[{id:19,name:'Bronze Studio',room_type:'Studio',active:true,
   availability:'enquire',image_url:'/accom-template/assets/studio.webp',
   size_sqm:18,kitchen:'Private kitchenette',bathroom:'Private',
   tenancies:[{weeks:51,start:'Sep 2027',end:'Sep 2028',weekly:289,illustrative:true},
              {weeks:44,start:'Sep 2027',end:'Jul 2028',weekly:305,illustrative:true}]
 }]
};
globalThis.document={getElementById:id=>id==='accom-property-data'?{textContent:JSON.stringify(fake)}:null}
const data=await import('../public/accom-template/data.js')

test('database snapshot becomes repeatable gallery and room contract options',()=>{
 assert.equal(data.snapshot.id,9)
 assert.equal(data.media.length,1)
 assert.equal(data.media[0].layout,'large')
 assert.equal(data.rooms.length,1)
 assert.equal(data.rooms[0].tenancies.length,2)
 assert.equal(data.rooms[0].tenancies[1].weekly,305)
 assert.equal(data.totalRent(289,51),14739)
 assert.equal(data.filterRooms(data.rooms,'studio').length,1)
 assert.equal(data.filterRooms(data.rooms,'ensuite').length,0)
});
test('untrusted labels do not become active markup in room sections',()=>{
 assert.ok(data.property.name.includes('&lt;script&gt;'))
 assert.equal(data.formatMoney(null),'Price on request')
 assert.equal(data.formatMoney(289),'£289')
});
test('enquiry validation checks name, email and explicit consent',()=>{
 assert.deepEqual(Object.keys(data.validateInquiry({name:'',email:'bad',consent:false})),['name','email','consent'])
 assert.deepEqual(data.validateInquiry({name:'Student',email:'student@example.net',consent:true}),{})
});
