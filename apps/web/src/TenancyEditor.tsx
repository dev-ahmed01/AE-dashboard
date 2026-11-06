import React from 'react'

export type Tenancy={weeks:number;start:string;end:string;weekly:number|null;availability:string;illustrative:boolean}

export default function TenancyEditor({value,onChange}:{value:Tenancy[];onChange:(next:Tenancy[])=>void}){
 const items=value||[]
 const set=(index:number,change:Partial<Tenancy>)=>onChange(items.map((item,i)=>i===index?{...item,...change}:item))
 return <section className="tenancy-editor">
  <div className="tenancy-editor-heading"><div><strong>Tenancy options</strong>
   <small>Each room can have multiple contract lengths. Rates marked illustrative cannot be published.</small></div>
   <button type="button" className="outline" disabled={items.length>=12}
     onClick={()=>onChange([...items,{weeks:51,start:'',end:'',weekly:null,availability:'Confirm availability',illustrative:false}])}>+ Add tenancy</button></div>
  {items.map((t,i)=><fieldset key={i} className="tenancy-edit-card">
   <legend>Tenancy {i+1}</legend>
   <div className="form-grid">
    <label>Length (weeks)<input type="number" min={0} max={104} value={t.weeks}
      onChange={e=>set(i,{weeks:Number(e.target.value)})}/></label>
    <label>Weekly rate (£)<input type="number" min={0} step=".01" value={t.weekly??''}
      onChange={e=>set(i,{weekly:e.target.value?Number(e.target.value):null})}/></label>
    <label>Start date / label<input value={t.start} onChange={e=>set(i,{start:e.target.value})}/></label>
    <label>End date / label<input value={t.end} onChange={e=>set(i,{end:e.target.value})}/></label>
   </div>
   <label>Availability details<input value={t.availability||''}
     onChange={e=>set(i,{availability:e.target.value})}/></label>
   <label className="checkline"><input type="checkbox" checked={!!t.illustrative}
     onChange={e=>set(i,{illustrative:e.target.checked})}/> Illustrative price / dates — not verified</label>
   <button className="outline" type="button" onClick={()=>onChange(items.filter((_,j)=>i!==j))}>Remove tenancy</button>
  </fieldset>)}
  {!items.length&&<p>No tenancy options yet. Students will see “Price on request”.</p>}
 </section>
}
