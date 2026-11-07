import {useEffect,useRef,useState, type ReactNode} from 'react'
import {ArrowDown,ArrowUp,ChevronDown,Plus,Trash2} from 'lucide-react'

/** Editor-owned ordered groups: collapsing them never drops unsaved values. */
export default function RepeatableField<T>({title,items,create,onChange,render,describe,help}:{
  title:string;items:T[];create:()=>T;onChange:(items:T[])=>void;
  render:(item:T,change:(value:T)=>void,index:number)=>ReactNode;
  describe?:(item:T,index:number)=>string;help?:string;
}){
  const [expanded,setExpanded]=useState(items.length>0&&items.length<=5)
  const previousCount=useRef(items.length)
  useEffect(()=>{
    // Hydration of a template sample happens after the first editor render.
    // Make the newly filled repeaters visible without forcing huge inventories open.
    if(previousCount.current===0&&items.length>0&&items.length<=5)setExpanded(true)
    previousCount.current=items.length
  },[items.length])
  const change=(index:number,value:T)=>onChange(items.map((item,i)=>i===index?value:item))
  const move=(index:number,by:number)=>{
    const next=[...items];const destination=index+by
    if(destination<0||destination>=next.length)return
    ;[next[index],next[destination]]=[next[destination],next[index]]
    onChange(next)
  }
  const add=()=>{onChange([...items,create()]);setExpanded(true)}
  return <section className="repeater-group" aria-label={title}>
    <div className="repeater-heading">
      <button type="button" className="repeater-toggle" aria-expanded={expanded} onClick={()=>setExpanded(v=>!v)}>
        <ChevronDown size={18} className={expanded?'is-expanded':''}/>
        <span><strong>{title}</strong> <small>({items.length})</small>{help&&<em>{help}</em>}</span>
      </button>
      <button type="button" className="outline repeater-add" onClick={add}><Plus size={15}/> Add another</button>
    </div>
    {expanded&&<div className="repeater-items">{items.map((item,index)=><div className="repeater-item" key={index}>
      <div className="repeater-item-head"><span><b>{String(index+1).padStart(2,'0')}</b> {describe?.(item,index)||`Item ${index+1}`}</span>
        <div className="repeater-actions"><button type="button" title="Move up" aria-label={`Move ${title} item ${index+1} up`} disabled={index===0} onClick={()=>move(index,-1)}><ArrowUp size={15}/></button>
          <button type="button" title="Move down" aria-label={`Move ${title} item ${index+1} down`} disabled={index===items.length-1} onClick={()=>move(index,1)}><ArrowDown size={15}/></button>
          <button type="button" title="Remove" aria-label={`Remove ${title} item ${index+1}`} onClick={()=>onChange(items.filter((_,i)=>i!==index))}><Trash2 size={15}/></button>
        </div></div>
      <div className="repeater-fields">{render(item,value=>change(index,value),index)}</div>
    </div>)}{items.length===0&&<p className="repeater-empty">No entries yet. Choose “Add another” to create the first one.</p>}</div>}
  </section>
}
