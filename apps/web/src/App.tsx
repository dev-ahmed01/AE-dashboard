import {useEffect,useMemo,useRef,useState} from 'react'
import {ArrowRight,Check,ChevronDown,ChevronLeft,ChevronRight,Compass,Heart,Home,Image as ImageIcon,LayoutDashboard,MapPin,Menu,Search,ShieldCheck,SlidersHorizontal,Sparkles,Users,Wallet,Upload,X} from 'lucide-react'
import RepeatableField from './RepeatableField'
import TenancyEditor, {type Tenancy} from './TenancyEditor'

type Room={id:number;property_id:number;name:string;room_type:string;details:string;size_sqm:number|null;kitchen:string;bathroom:string;price:number|null;currency:string;price_period:string;available_from:string|null;availability:string;rate_checked_at:string|null;source_url:string;image_url:string;image_alt?:string;image_layout?:'regular'|'large';edit_version:number;active:boolean;tenancies?:Tenancy[]}
type Pair={question:string;answer:string}
type Landmark={name:string;detail:string}
type Media={url:string;alt:string;category?:string;layout?:'regular'|'large'}
type MasterField={key:string;section:string;kind:'text'|'textarea'|'cta_label'|'cta_link'|'image'|'image_alt';label:string;group:string;value:string}
type MasterSection={id:string;title:string;fields:MasterField[]}
type Property={id:number;name:string;slug:string;city:string;country:string;address:string;postcode:string;university:string;description:string;gallery:Media[];content_overrides?:Record<string,string>;published:boolean;archived:boolean;is_demo?:boolean;edit_version:number;price_note?:string;verified_at:string|null;from_price:number|null;currency:string;price_period:string;highlights?:string[];highlight_descriptions?:string[];amenities?:string[];policies?:Pair[];faq?:Pair[];landmarks?:Landmark[];floorplans?:Media[];tour_url?:string;offers?:{title:string;description:string;valid_until?:string}[];reviews?:{name:string;quote:string;source_url:string}[];review_source_url?:string;review_score?:number|null;review_count?:number|null;seo_title?:string;meta_description?:string;noindex?:boolean;rooms?:Room[]}
type User={id:number;name:string;email:string;role:string}
type LoginResult={token:string;user:User}
type Enquiry={id:number;property:string;property_id:number;room_id:number|null;name:string;email:string;phone:string;university:string;move_in_date:string|null;message:string;status:string;assigned_to_id:number|null;created_at:string}
type Overview={user:User;saved:Property[];enquiries:{id:number;property:string;status:string;assigned_consultant:string|null;created_at:string}[];cashback:{enquiry_id:number;amount:number|null;currency:string;status:string}[]}

let token=sessionStorage.getItem('accom_token')||''
async function api<T>(path:string,options:RequestInit={}):Promise<T>{
 const headers:Record<string,string>={...(options.headers as Record<string,string>||{})}
 if(!(options.body instanceof FormData))headers['Content-Type']='application/json'
 if(token)headers.Authorization=`Bearer ${token}`
 const response=await fetch(path,{...options,headers})
 if(!response.ok){const detail=await response.json().catch(()=>({detail:'Request failed'}));throw new Error(typeof detail.detail==='string'?detail.detail:`Request failed (${response.status})`)}
 return response.json() as Promise<T>
}
async function uploadPhoto(file:File):Promise<string>{
 const form=new FormData();form.append('file',file)
 const result=await api<{url:string}>('/api/admin/media',{method:'POST',body:form})
 return result.url
}
const money=(amount:number|null|undefined,currency='GBP',period='week')=>amount===null||amount===undefined?'Price on request':`${new Intl.NumberFormat('en-GB',{style:'currency',currency,maximumFractionDigits:0}).format(amount)}/${period==='week'?'wk':'mo'}`
const absolute=(url?:string)=>!!url&&(/^(https:\/\/|\/api\/media\/[0-9]+$|\/accom-template\/assets\/[a-z0-9_-]+\.(webp|png|jpg)$)/i.test(url))
const fmt=(d?:string|null)=>d?new Date(d).toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'}):'To confirm'
const readPath=()=>window.location.pathname
type Offer={title:string;description:string;valid_until?:string}
type Review={name:string;quote:string;source_url:string}
const defaults={name:'',slug:'',is_demo:false,city:'',country:'United Kingdom',address:'',postcode:'',university:'',description:'',content_overrides:{} as Record<string,string>,published:false,noindex:false,seo_title:'',meta_description:'',gallery:[] as Media[],amenities:[] as string[],highlights:[] as string[],highlight_descriptions:[] as string[],policies:[] as Pair[],faq:[] as Pair[],landmarks:[] as Landmark[],floorplans:[] as Media[],tour_url:'',offers:[] as Offer[],reviews:[] as Review[],review_source_url:'',review_score:null as number|null,review_count:null as number|null}
const blankRoom={name:'',room_type:'En suite',details:'',size_sqm:null as number|null,kitchen:'Shared',bathroom:'Private',price:null as number|null,currency:'GBP',price_period:'week',available_from:null as string|null,availability:'enquire',rate_checked_at:null as string|null,source_url:'',image_url:'',image_alt:'',image_layout:'regular' as 'regular'|'large',active:true,tenancies:[] as Tenancy[]}

function Logo(){return <span className="brand"><span className="brand-icon">a<span>.</span></span><span className="brand-text">accom<small>BY EMLEN</small></span></span>}
function Photo({url,alt,className=''}:{url?:string;alt?:string;className?:string}){return url&&absolute(url)?<img className={className} src={url} alt={alt||'Accommodation'} loading="lazy"/>:<div className={`photo-fallback ${className}`}><Home size={28}/><span>Property image</span></div>}
function Badge({children}:{children:React.ReactNode}){return <span className="badge">{children}</span>}
function Header({go,user,logout,hideExplore=false}:{go:(s:string)=>void;user:User|null;logout:()=>void;hideExplore?:boolean}){return <header className="site-header"><div className="header-inner"><button className="brand-link" onClick={()=>go('/')} aria-label="Accom home"><Logo/></button><nav>{!hideExplore&&<button onClick={()=>go('/')}>Explore stays</button>}{user?.role==='student'&&<button onClick={()=>go('/student')}>My journey</button>}{user&&user.role!=='student'&&<button onClick={()=>go('/admin')}>Dashboard</button>}</nav><div className="nav-actions">{user?<><span className="hello">{user.name}</span><button className="outline tiny" onClick={logout}>Log out</button></>:<button className="outline tiny" onClick={()=>go('/login')}>Sign in</button>}<button className="nav-main" onClick={()=>go(user?.role==='student'?'/student':'/help')}>{user?.role==='student'?'My account':'Get help'} <ArrowRight size={15}/></button></div></div></header>}
function PropertyCard({p,go,save}:{p:Property;go:(s:string)=>void;save:(id:number)=>void}){return <article className="property-card"><button className="property-photo" onClick={()=>go('/property/'+p.slug)}><Photo url={p.gallery?.[0]?.url} alt={p.gallery?.[0]?.alt||p.name}/><span className="image-tag">Student accommodation</span></button><div className="property-card-body"><div className="card-meta"><MapPin size={14}/>{p.city}, {p.country}</div><h3>{p.name}</h3><p>{p.university||p.address||'Explore this property and its rooms'}</p><div className="property-bottom"><div><span className="muted">Rooms from</span><strong>{money(p.from_price,p.currency,p.price_period)}</strong></div><div className="card-actions"><button className="heart-button" aria-label={`Save ${p.name}`} title="Save property" onClick={()=>save(p.id)}><Heart size={19}/></button><button className="primary compact" onClick={()=>go('/property/'+p.slug)}>View rooms <ArrowRight size={15}/></button></div></div></div></article>}
function Directory({go,user}:{go:(s:string)=>void;user:User|null}){const [results,setResults]=useState<Property[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState(''),[q,setQ]=useState(''),[city,setCity]=useState(''),[university,setUniversity]=useState(''),[kind,setKind]=useState(''),[budget,setBudget]=useState(''),[applied,setApplied]=useState(0)
 useEffect(()=>{const params=new URLSearchParams();if(q)params.set('q',q);if(city)params.set('city',city);if(university)params.set('university',university);if(kind)params.set('room_type',kind);if(budget)params.set('max_price',budget);setLoading(true);api<Property[]>('/api/properties?'+params).then(setResults).catch(e=>setError(e.message)).finally(()=>setLoading(false))},[applied])
 const save=async(id:number)=>{if(!user){go('/login');return}try{await api('/api/me/saved/'+id,{method:'POST'});alert('Added to your shortlist')}catch(e){alert((e as Error).message)}}
 return <main><section className="directory-hero"><div className="wrap"><span className="eyebrow">STUDENT LIVING · MADE SIMPLE</span><h1>Find a place that feels <em>like yours.</em></h1><p>Explore student residences, compare real room options and ask the right questions before moving in.</p><div className="search-panel"><label><Search size={18}/><input placeholder="Search property, city or university" value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>e.key==='Enter'&&setApplied(x=>x+1)} /></label><button className="primary" onClick={()=>setApplied(x=>x+1)}>Find my room <ArrowRight size={17}/></button></div></div></section><section className="wrap results"><div className="section-intro"><span className="eyebrow">EXPLORE ACCOMMODATION</span><h2>Spaces worth coming home to.</h2><p>Use the filters to narrow your options. Prices and availability are only shown when entered and dated by the Accom team.</p></div><div className="filters"><div className="filter-label"><SlidersHorizontal size={16}/> Filters</div><input aria-label="City" placeholder="City" value={city} onChange={e=>setCity(e.target.value)}/><input aria-label="University" placeholder="University" value={university} onChange={e=>setUniversity(e.target.value)}/><select aria-label="Room type" value={kind} onChange={e=>setKind(e.target.value)}><option value="">All rooms</option><option>En suite</option><option>Studio</option></select><input aria-label="Maximum weekly or monthly price" type="number" min="0" placeholder="Max price" value={budget} onChange={e=>setBudget(e.target.value)}/><button className="outline" onClick={()=>setApplied(x=>x+1)}>Apply</button></div><div className="result-heading">{loading?'Loading accommodation…':`${results.length} ${results.length===1?'property':'properties'} found`}</div>{error&&<p className="error">{error}</p>}{!loading&&!results.length?<div className="empty-state"><Home size={33}/><h3>No published listings match yet.</h3><p>Change your filters, or ask Accom for help. Properties will appear here when the team publishes them from the dashboard.</p><button className="outline" onClick={()=>{setQ('');setCity('');setUniversity('');setKind('');setBudget('');setApplied(x=>x+1)}}>Clear filters</button></div>:<div className="property-grid">{results.map(p=><PropertyCard key={p.id} p={p} go={go} save={save}/>)}</div>}</section></main>}
function EnquiryModal({p,room,close,onSent}:{p:Property;room:Room|null;close:()=>void;onSent:()=>void}){const [name,setName]=useState(''),[email,setEmail]=useState(''),[phone,setPhone]=useState(''),[uni,setUni]=useState(''),[move,setMove]=useState(''),[message,setMessage]=useState(''),[consent,setConsent]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[done,setDone]=useState(false)
 const submit=async(e:React.FormEvent)=>{e.preventDefault();setBusy(true);setError('');try{await api('/api/enquiries',{method:'POST',body:JSON.stringify({property_id:p.id,room_id:room?.id||null,name,email,phone,university:uni,move_in_date:move||null,message,consent})});setDone(true);onSent()}catch(err){setError((err as Error).message)}finally{setBusy(false)}}
 return <div className="modal-overlay" role="presentation" onMouseDown={e=>e.target===e.currentTarget&&close()}><div className="modal" role="dialog" aria-modal="true" aria-labelledby="enquire-heading"><button className="close-modal" onClick={close} aria-label="Close"><X/></button>{done?<div className="success-state"><Check size={36}/><h2>Enquiry received.</h2><p>Accom can now review your question about {room?.name||p.name}. This is not a booking confirmation.</p><button className="primary" onClick={close}>Return to listing</button></div>:<><span className="eyebrow">PERSONAL SUPPORT</span><h2 id="enquire-heading">Ask about {room?.name||p.name}.</h2><p>Tell Accom what you need to know. No payment is taken here.</p><form className="form-grid" onSubmit={submit}><label>Your name<input required value={name} onChange={e=>setName(e.target.value)} minLength={2}/></label><label>Email address<input type="email" required value={email} onChange={e=>setEmail(e.target.value)}/></label><label>Phone (optional)<input value={phone} onChange={e=>setPhone(e.target.value)}/></label><label>University (optional)<input value={uni} onChange={e=>setUni(e.target.value)}/></label><label>Preferred move-in date<input type="date" value={move} onChange={e=>setMove(e.target.value)}/></label><label className="full">Your question<textarea rows={3} value={message} onChange={e=>setMessage(e.target.value)}/></label><label className="consent full"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)} required/><span>I agree that Accom may contact me about this enquiry.</span></label>{error&&<p className="error full">{error}</p>}<button className="primary full" disabled={busy}>{busy?'Sending…':'Send enquiry'} <ArrowRight size={16}/></button></form></>}</div></div>}
function Listing({slug,go,user,previewData}:{slug:string;go:(s:string)=>void;user:User|null;previewData?:Property|null}){const [p,setP]=useState<Property|null>(previewData||null),[error,setError]=useState(''),[tab,setTab]=useState('overview'),[gallery,setGallery]=useState(-1),[room,setRoom]=useState<Room|null>(null),[enquiry,setEnquiry]=useState(false),[compare,setCompare]=useState<number[]>([]),[compareOpen,setCompareOpen]=useState(false),[roomFilter,setRoomFilter]=useState('All'),[faqSearch,setFaqSearch]=useState(''),[costs,setCosts]=useState([0,0,0,0,0]),[weeks,setWeeks]=useState(44)
 useEffect(()=>{(previewData?Promise.resolve(previewData):api<Property>('/api/properties/'+encodeURIComponent(slug))).then(setP).catch(e=>setError(e.message))},[slug,previewData])
 useEffect(()=>{if(!p)return;document.title=(p.seo_title||p.name+' | Accom by Emlen');},[p])
 const galleryPhotos=p?.gallery?.filter(g=>absolute(g.url))||[];const roomList=(p?.rooms||[]).filter(r=>r.active&&(roomFilter==='All'||r.room_type===roomFilter));const costSum=costs.reduce((a,b)=>a+b,0)
 const seeSection=(name:string)=>{setTab(name);document.getElementById(name)?.scrollIntoView({behavior:'smooth',block:'start'})}
 const toggleCompare=(id:number)=>setCompare(cur=>cur.includes(id)?cur.filter(x=>x!==id):cur.length<2?[...cur,id]:cur)
 const save=async()=>{if(!user){go('/login');return}try{await api('/api/me/saved/'+p!.id,{method:'POST'});alert('Saved to your student portal')}catch(e){alert((e as Error).message)}}
 if(error)return <main className="wrap empty-state"><h2>Listing unavailable</h2><p>{error}</p><button onClick={()=>go('/')} className="outline">Back to accommodation</button></main>
 if(!p)return <main className="wrap loading">Loading property details…</main>
 const currentRoom=p.rooms?.find(r=>r.id===compare[0]);const secondRoom=p.rooms?.find(r=>r.id===compare[1])
 return <main><div className="wrap listing-head"><div className="breadcrumbs"><button onClick={()=>go('/')}>Student accommodation</button><ChevronRight size={13}/>{p.city}<ChevronRight size={13}/>{p.name}</div><div className="listing-title-row"><div><span className="eyebrow">YOUR NEXT PLACE</span><h1>{p.name}</h1><p><MapPin size={16}/>{[p.address,p.postcode,p.city].filter(Boolean).join(', ')}</p>{p.review_score!==null&&p.review_score!==undefined&&p.review_source_url&&<a className="review-link" href={p.review_source_url} rel="noopener noreferrer" target="_blank">★ {p.review_score}/5 · {p.review_count??'View'} source reviews</a>}</div><div className="title-actions"><button className="outline" onClick={save}><Heart size={16}/> Save</button><button className="outline" onClick={()=>navigator.clipboard?.writeText(window.location.href)}>Share</button></div></div></div><section className={'wrap listing-gallery gallery-dynamic '+((p.gallery?.length||0)<=1?'gallery-one':'')} aria-label="Property photo gallery">{(p.gallery?.length?p.gallery:[{url:'',alt:'Property image',layout:'large' as const}]).slice(0,5).map((photo,i)=><button key={i} className={'gallery-tile '+((photo.layout||(i===0?'large':'regular'))==='large'?'is-large':'is-regular')} aria-label={`View property photo ${i+1}${photo.category?' — '+photo.category:''}`} onClick={()=>setGallery(i)}><Photo url={photo.url} alt={photo.alt||p.name}/></button>)}<button className="gallery-all" onClick={()=>setGallery(0)}><ImageIcon size={16}/> View gallery {p.gallery?.length||0}</button></section><div className="wrap listing-grid"><div className="listing-main"><nav className="section-nav" aria-label="Property sections">{[['overview','Overview'],['rooms','Rooms'],['amenities','Included'],['policies','Terms'],['location','Location'],['faqs','FAQs'],['reviews','Reviews']].map(([id,title])=><button key={id} className={tab===id?'active':''} onClick={()=>seeSection(id)}>{title}</button>)}</nav><section id="overview" className="listing-section"><span className="eyebrow">THE RESIDENCE</span><h2>Make yourself at home.</h2><p className="lede">{p.description||'Explore the rooms, included amenities and important policies before making an enquiry.'}</p><div className="highlight-grid">{(p.highlights||[]).map((h,i)=><div key={i} className="glass-highlight"><Check size={16}/><strong>{h}</strong></div>)}</div>{p.tour_url&&absolute(p.tour_url)&&<a className="inline-link" href={p.tour_url} rel="noopener noreferrer" target="_blank">Explore official virtual tour <ArrowRight size={15}/></a>}</section><section id="rooms" className="listing-section"><span className="eyebrow">FIND YOUR FIT</span><div className="section-split"><div><h2>Choose your room.</h2><p>Compare privacy, size and rate snapshots. Confirm the full contract before booking.</p></div><div className="pills">{['All','En suite','Studio'].map(t=><button key={t} className={t===roomFilter?'selected':''} onClick={()=>setRoomFilter(t)}>{t}</button>)}</div></div>{roomList.length?<div className="rooms-list">{roomList.map(r=><article key={r.id} className={'room-card '+(r.image_layout==='large'?'room-card-large':'room-card-regular')}><Photo url={r.image_url} alt={r.image_alt||r.name}/><div className="room-details"><Badge>{r.room_type}</Badge><h3>{r.name}</h3><p>{[r.size_sqm?`${r.size_sqm} m²`:null,r.bathroom&&`${r.bathroom} bathroom`,r.kitchen&&`${r.kitchen} kitchen`].filter(Boolean).join(' · ')}</p>{r.details&&<p>{r.details}</p>}<div className="room-actions"><button onClick={()=>toggleCompare(r.id)} className="link-button">{compare.includes(r.id)?'✓ Added to compare':'＋ Compare'}</button><button onClick={()=>{setRoom(r);setEnquiry(true)}} className="outline">Enquire about this room</button></div></div><div className="rate"><small>{r.rate_checked_at?'LISTING SNAPSHOT':'RATE TO CONFIRM'}</small><strong>{money(r.price,r.currency,r.price_period)}</strong><span>{r.availability==='available'?`Available from ${fmt(r.available_from)}`:r.availability==='unavailable'?'Currently unavailable':'Confirm availability'}</span>{r.rate_checked_at&&<span>Rate checked {fmt(r.rate_checked_at)}</span>}</div></article>)}</div>:<div className="empty-inline">No matching room types are published yet.</div>}{compare.length>0&&<div className="compare-bar"><span>{compare.length} room{compare.length>1?'s':''} selected</span><button className="outline" onClick={()=>setCompareOpen(true)}>Compare rooms</button><button className="link-button" onClick={()=>setCompare([])}>Clear</button></div>}</section><section id="amenities" className="listing-section"><span className="eyebrow">LIFE MADE EASIER</span><h2>What's included.</h2><div className="amenity-grid">{(p.amenities||[]).map((a,i)=><div key={i}><Check size={18}/>{a}</div>)}</div>{!(p.amenities?.length)&&<p>Ask Accom for the current amenity list.</p>}<div className="budget-box"><div><span className="eyebrow">BUDGET TOOL</span><h3>Compare your own weekly bills.</h3><p>This is your personal estimate—not a guaranteed saving.</p></div><div className="budget-fields">{['Wi-Fi','Electricity','Heating','Water','Insurance'].map((label,i)=><label key={label}>{label}<div>£<input type="number" min="0" value={costs[i]||''} onChange={e=>setCosts(cur=>cur.map((v,n)=>n===i?Math.max(0,Number(e.target.value)||0):v))}/></div></label>)}</div><div className="budget-result"><strong>£{costSum} / week</strong><span>£{costSum*weeks} over {weeks} weeks</span><div className="pills">{[44,51].map(w=><button className={weeks===w?'selected':''} onClick={()=>setWeeks(w)} key={w}>{w} weeks</button>)}</div></div></div></section><section id="policies" className="listing-section"><span className="eyebrow">READ BEFORE YOU DECIDE</span><h2>Terms, policies & offers.</h2>{(p.offers||[]).map((o,i)=><div className="offer" key={i}><Sparkles size={19}/><div><strong>{o.title}</strong><p>{o.description}</p></div></div>)}{(p.policies||[]).map((x,i)=><details key={i}><summary>{x.question}<ChevronDown size={16}/></summary><p>{x.answer}</p></details>)}{!p.policies?.length&&<p>Request the latest cancellation, payment and visitor policies from the accommodation provider before paying.</p>}{(p.floorplans||[]).length>0&&<div className="floorplans"><h3>Floor plans</h3>{p.floorplans!.map((f,i)=><a key={i} href={f.url} target="_blank" rel="noopener noreferrer">{f.alt||`Floor plan ${i+1}`} <ArrowRight size={14}/></a>)}</div>}</section><section id="location" className="listing-section"><span className="eyebrow">YOUR NEIGHBOURHOOD</span><h2>Location & nearby landmarks.</h2><p><MapPin size={16}/>{[p.address,p.city,p.postcode].filter(Boolean).join(', ')}</p><div className="landmarks">{(p.landmarks||[]).map((x,i)=><div key={i}><strong>{x.name}</strong><span>{x.detail}</span></div>)}</div><a href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent([p.address,p.city,p.postcode].join(' '))}`} className="inline-link" target="_blank" rel="noopener noreferrer">Check live directions <ArrowRight size={16}/></a></section><section id="faqs" className="listing-section"><span className="eyebrow">QUESTIONS ANSWERED</span><h2>Before you decide.</h2><input aria-label="Search FAQ" className="faq-search" placeholder="Search questions…" value={faqSearch} onChange={e=>setFaqSearch(e.target.value)}/>{(p.faq||[]).filter(f=>(f.question+' '+f.answer).toLowerCase().includes(faqSearch.toLowerCase())).map((f,i)=><details key={i}><summary>{f.question}<ChevronDown size={16}/></summary><p>{f.answer}</p></details>)}{!p.faq?.length&&<p>Contact Accom to ask about guarantors, check-in and cancellation terms.</p>}</section><section id="reviews" className="listing-section"><span className="eyebrow">STUDENT VOICES</span><h2>Reviews & trust.</h2>{p.review_source_url&&<p>View attributed third-party reviews <a className="inline-link" href={p.review_source_url} target="_blank" rel="noopener noreferrer">at the original source <ArrowRight size={15}/></a></p>}{(p.reviews||[]).map((r,i)=><blockquote className="review" key={i}><p>“{r.quote}”</p><strong>{r.name}</strong>{absolute(r.source_url)&&<a href={r.source_url} target="_blank" rel="noopener noreferrer">Original review</a>}</blockquote>)}{!p.reviews?.length&&!p.review_source_url&&<p>Verified reviews are not currently published for this listing.</p>}</section></div><aside className="listing-aside"><div className="sticky-offer"><span className="eyebrow">STUDENT ACCOMMODATION</span><small>Rooms from</small><strong>{money(p.from_price,p.currency,p.price_period)}</strong><p>Weekly or monthly rate is determined by the room. Confirm exact availability and the total contract cost.</p><button className="primary" onClick={()=>{setRoom(null);setEnquiry(true)}}>Enquire about this property <ArrowRight size={16}/></button><button className="outline" onClick={()=>seeSection('rooms')}>Explore room types</button><div className="offer-divider"></div><div className="trust-line"><ShieldCheck size={18}/> No accommodation rent collected here</div><div className="trust-line"><Users size={18}/> Enquiry handled by the Accom team</div>{!p.verified_at&&<div className="needs-check">Latest rates and listing details should be confirmed before making decisions.</div>}</div></aside></div>{enquiry&&<EnquiryModal p={p} room={room} close={()=>setEnquiry(false)} onSent={()=>{}}/>}{gallery>=0&&<div className="lightbox" role="dialog" aria-modal="true" aria-label="Property photo gallery"><div className="lightbox-head"><strong>{p.name} · Photo gallery</strong><button onClick={()=>setGallery(-1)}><X/></button></div>{galleryPhotos.length?<div className="lightbox-view"><button aria-label="Previous photo" onClick={()=>setGallery(i=>(i-1+galleryPhotos.length)%galleryPhotos.length)}><ChevronLeft size={30}/></button><img src={galleryPhotos[gallery%galleryPhotos.length].url} alt={galleryPhotos[gallery%galleryPhotos.length].alt||p.name}/><button aria-label="Next photo" onClick={()=>setGallery(i=>(i+1)%galleryPhotos.length)}><ChevronRight size={30}/></button></div>:<div className="lightbox-empty">Approved property photographs have not been uploaded.</div>}<p>{galleryPhotos.length?`${gallery+1} / ${galleryPhotos.length}`:'No photos available'}</p></div>}{compareOpen&&<div className="modal-overlay" role="presentation" onMouseDown={e=>e.target===e.currentTarget&&setCompareOpen(false)}><div className="modal compare-modal" role="dialog" aria-modal="true" aria-label="Compare room types"><button className="close-modal" onClick={()=>setCompareOpen(false)}><X/></button><span className="eyebrow">SIDE BY SIDE</span><h2>Compare your rooms.</h2><div className="comparison-table"><div>Room</div><strong>{currentRoom?.name||'—'}</strong><strong>{secondRoom?.name||'Select another room'}</strong>{(['room_type','size_sqm','kitchen','bathroom','price','availability'] as const).map(k=><div className="compare-row" key={k}><span>{k.replace('_',' ')}</span><span>{k==='price'?money(currentRoom?.price,currentRoom?.currency,currentRoom?.price_period):String(currentRoom?.[k]??'To confirm')}</span><span>{k==='price'?money(secondRoom?.price,secondRoom?.currency,secondRoom?.price_period):String(secondRoom?.[k]??'To confirm')}</span></div>)}</div></div></div>}</main>}
function Auth({go,setUser,registration=false}:{go:(s:string)=>void;setUser:(u:User)=>void;registration?:boolean}){
 const register=registration;
 const [name,setName]=useState(''),[identifier,setIdentifier]=useState(''),[email,setEmail]=useState(''),[username,setUsername]=useState(''),[password,setPassword]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState(''),[info,setInfo]=useState('');
 const submit=async(e:React.FormEvent)=>{e.preventDefault();setBusy(true);setError('');setInfo('');try{
  const result=await api<LoginResult&{verification_required?:boolean;message?:string}>(register?'/api/auth/register':'/api/auth/login',{
   method:'POST',body:JSON.stringify(register?{name,email,username:username.trim()||null,password}:{identifier:identifier.trim(),password})
  });
  if(result.verification_required){setInfo(result.message||'Verify your email address to activate your student account.');return}
  token=result.token;sessionStorage.setItem('accom_token',token);setUser(result.user);go(result.user.role==='student'?'/student':'/admin')
 }catch(e){setError((e as Error).message)}finally{setBusy(false)}};
 return <main className="auth-page"><div className="auth-card"><span className="eyebrow">WELCOME TO ACCOM</span><h1>{register?'Create your account.':'Good to have you back.'}</h1>{register&&<p>Save properties and track your accommodation enquiries in one place.</p>}
 <form onSubmit={submit} className="auth-form">
 {register?<><label>Full name<input required minLength={2} autoComplete="name" value={name} onChange={e=>setName(e.target.value)}/></label><label>Email address<input type="email" required autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)}/></label><label>Username (optional)<input type="text" autoComplete="username" minLength={3} maxLength={32} pattern="[A-Za-z][A-Za-z0-9_.-]{2,31}" title="3–32 letters, numbers, underscores, hyphens or dots. Begin with a letter." value={username} onChange={e=>setUsername(e.target.value)} placeholder="Choose a username"/></label></>:<label>Email or username<input type="text" required autoComplete="username" value={identifier} onChange={e=>setIdentifier(e.target.value)} placeholder="Email address or username"/></label>}
 <label>Password<input type="password" required autoComplete={register?'new-password':'current-password'} minLength={register?12:1} value={password} onChange={e=>setPassword(e.target.value)} placeholder={register?'At least 12 characters':''}/></label>
 {error&&<p className="error" role="alert">{error}</p>}{info&&<p className="notice" role="status">{info}</p>}
 <button disabled={busy} className="primary">{busy?'Checking…':register?'Create account':'Sign in'} <ArrowRight size={17}/></button>
 </form>{register&&<button type="button" className="text-link" onClick={()=>go('/login')}>Already have an account? Sign in</button>}</div></main>
}
function Student({go,user}:{go:(s:string)=>void;user:User|null}){const [data,setData]=useState<Overview|null>(null),[error,setError]=useState('');useEffect(()=>{if(user?.role==='student')api<Overview>('/api/me/overview').then(setData).catch(e=>setError(e.message))},[user]);if(!user)return <div className="wrap empty-state"><h2>Your student journey starts here.</h2><p>Sign in to save accommodation and track your enquiries.</p><button className="primary" onClick={()=>go('/login')}>Sign in or register</button></div>;if(user.role!=='student')return <div className="wrap empty-state"><h2>Student-only area</h2><button onClick={()=>go('/admin')} className="outline">Go to dashboard</button></div>;return <main className="wrap portal"><span className="eyebrow">YOUR PERSONAL SPACE</span><h1>Hello, {user.name.split(' ')[0]}.</h1><p>Everything about your accommodation search in one place.</p>{error&&<p className="error">{error}</p>}<div className="portal-stats"><div><strong>{data?.saved.length??'—'}</strong><span>Saved properties</span></div><div><strong>{data?.enquiries.length??'—'}</strong><span>Enquiries</span></div><div><strong>{data?.cashback.length??'—'}</strong><span>Cashback records</span></div></div><div className="portal-columns"><section className="panel"><div className="panel-header"><h2>My shortlist</h2><button onClick={()=>go('/')}>Explore stays <ArrowRight size={14}/></button></div>{data?.saved.length?data.saved.map(p=><button className="item-row" key={p.id} onClick={()=>go('/property/'+p.slug)}><Home size={18}/><span><strong>{p.name}</strong><small>{p.city}</small></span><ArrowRight size={16}/></button>):<p>No saved homes yet. Browse listings and tap the heart to build your shortlist.</p>}</section><section className="panel"><h2>Enquiry progress</h2>{data?.enquiries.length?data.enquiries.map(e=><div className="item-row" key={e.id}><Compass size={18}/><span><strong>{e.property}</strong><small>{e.assigned_consultant?'Consultant: '+e.assigned_consultant:'Consultant to be assigned'}</small></span><Badge>{e.status.replace('_',' ')}</Badge></div>):<p>Your enquiries will appear here once submitted. An enquiry is not a confirmed booking.</p>}</section><section className="panel"><h2>Cashback (if applicable)</h2>{data?.cashback.length?data.cashback.map(e=><div className="item-row" key={e.enquiry_id}><Wallet size={18}/><span><strong>{money(e.amount,e.currency,'week').split('/')[0]}</strong><small>Enquiry #{e.enquiry_id}</small></span><Badge>{e.status.replace('_',' ')}</Badge></div>):<p>No cashback eligibility or payout record has been confirmed for your enquiries.</p>}</section></div></main>}
type ProjectPage={file:string;route:string;type:string;headings:string[];cta_labels:string[];image_references:string[];fields:{kind:string;tag?:string;value:string}[];renderable_html:boolean;requires_build:boolean}
type ProjectInspection={filename:string;framework:string;pages:ProjectPage[];source_files:number;total_fields:number;renderable_pages:number;recommended_build_command:string;message:string}
type AccomTemplate={id:number;name:string;approved:boolean;sections:{id:string;name:string;order:number}[];fields:{key:string;section_id:string;label:string;kind:string;tag?:string;default:string;mode:'page'|'static'}[]}
type Editorial={id:number;kind:'editorial';template_id:number;title:string;slug:string;values:Record<string,string>;seo_title:string;meta_description:string;noindex:boolean;published:boolean;archived:boolean;edit_version:number}
type CashbackRow={id:number;enquiry_id:number;amount:number|null;currency:string;status:string;notes:string}
function Admin({go,user}:{go:(s:string)=>void;user:User|null}){
 const [tab,setTab]=useState<'All Pages'|'Add Page'|'Upload Template'>('All Pages')
 const [properties,setProperties]=useState<Property[]>([]),[pages,setPages]=useState<Editorial[]>([]),[templates,setTemplates]=useState<AccomTemplate[]>([])
 const [enquiries,setEnquiries]=useState<Enquiry[]>([]),[staff,setStaff]=useState<User[]>([]),[cashback,setCashback]=useState<CashbackRow[]>([])
 const [search,setSearch]=useState(''),[filter,setFilter]=useState<'All'|'Published'|'Draft'|'Archived'>('All')
 const [editing,setEditing]=useState<Property|null>(null),[creating,setCreating]=useState(false),[roomParent,setRoomParent]=useState<Property|null>(null),[room,setRoom]=useState<Room|null>(null)
 const [editEditorial,setEditEditorial]=useState<Editorial|null>(null),[preview,setPreview]=useState<Property|null>(null),[previewHTML,setPreviewHTML]=useState('')
 const [templateName,setTemplateName]=useState(''),[file,setFile]=useState<File|null>(null),[selectedTemplate,setSelectedTemplate]=useState<AccomTemplate|null>(null),[mappingFields,setMappingFields]=useState<AccomTemplate['fields']>([])
 const [inspection,setInspection]=useState<ProjectInspection|null>(null),[selectedSource,setSelectedSource]=useState('')
 const [addTemplatePreview,setAddTemplatePreview]=useState('')
 const templateFrameContainer=useRef<HTMLDivElement|null>(null)
 const [templateFrameScale,setTemplateFrameScale]=useState(.5)
 useEffect(()=>{
   const el=templateFrameContainer.current
   if(!el)return
   const update=()=>setTemplateFrameScale(Math.max(.2,Math.min(.9,(el.clientWidth-28)/1280)))
   update()
   const observer=new ResizeObserver(update);observer.observe(el)
   return()=>observer.disconnect()
 },[tab])
 const [pageTitle,setPageTitle]=useState(''),[pageTemplate,setPageTemplate]=useState('native-property')
 useEffect(()=>{
  if(pageTemplate==='native-property'){setAddTemplatePreview('');return}
  let active=true
  apiText('/api/admin/templates/'+pageTemplate+'/preview').then(html=>{if(active)setAddTemplatePreview(html)}).catch(()=>{if(active)setAddTemplatePreview('')})
  return()=>{active=false}
 },[pageTemplate])
 const [showOperations,setShowOperations]=useState(false)
 const [showApprovedDesign,setShowApprovedDesign]=useState(false)
 const [notice,setNotice]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false)
 const [selectedEnquiry,setSelectedEnquiry]=useState<number|null>(null),[notes,setNotes]=useState<{id:number;message:string;by:string;created_at:string}[]>([]),[noteText,setNoteText]=useState('')
 const [staffName,setStaffName]=useState(''),[staffEmail,setStaffEmail]=useState(''),[staffUsername,setStaffUsername]=useState(''),[staffPassword,setStaffPassword]=useState('')
 const [audit,setAudit]=useState<{event:string;reference:string;at:string;actor:string}[]>([])
 const report=(e:unknown)=>setError(e instanceof Error?e.message:String(e))
 const refresh=async()=>{
  try{
   const result=await Promise.all([
    api<Property[]>('/api/admin/properties'),api<Editorial[]>('/api/admin/pages'),api<AccomTemplate[]>('/api/admin/templates'),
    api<Enquiry[]>('/api/admin/enquiries'),api<User[]>('/api/admin/staff'),api<CashbackRow[]>('/api/admin/cashback')
   ])
   setProperties(result[0]);setPages(result[1]);setTemplates(result[2]);setEnquiries(result[3]);setStaff(result[4]);setCashback(result[5]);
   if(user?.role==='admin')api<typeof audit>('/api/admin/audit').then(setAudit).catch(()=>{})
  }catch(e){report(e)}
 }
 useEffect(()=>{if(user?.role==='admin'||user?.role==='editor')refresh()},[user])
 if(!user)return <main className="wrap empty-state"><h2>Staff sign-in required</h2><button className="primary" onClick={()=>go('/login')}>Sign in</button></main>
 if(user.role==='student')return <main className="wrap empty-state"><h2>Staff access only</h2><button onClick={()=>go('/student')} className="outline">My portal</button></main>
 const action=async(task:()=>Promise<unknown>,success:string)=>{setError('');setBusy(true);try{await task();await refresh();setNotice(success)}catch(e){report(e)}finally{setBusy(false)}}
 const filtered=[...properties.filter(p=>!p.is_demo).map(p=>({...p,kind:'property' as const,title:p.name})),...pages.map(p=>({...p,kind:'editorial' as const,name:p.title,city:'Editorial page',rooms:[] as Room[]}))]
  .filter(p=>(p.title+' '+p.slug).toLowerCase().includes(search.toLowerCase()))
  .filter(p=>(filter==='All'&&!p.archived)||(filter==='Archived'&&p.archived)||(filter==='Published'&&p.published&&!p.archived)||(filter==='Draft'&&!p.published&&!p.archived))
 const startEdit=(p:Property)=>{setEditing(p);setCreating(false)}
 const create=async()=>{
  if(pageTitle.trim().length<3){setError('Enter a page name of at least 3 characters.');return}
  if(!pageTemplate){setError('Choose a template.');return}
  if(pageTemplate==='native-property'){
   await action(async()=>{
    const created=await api<Property>('/api/admin/properties/draft',{method:'POST',body:JSON.stringify({name:pageTitle.trim()})})
    setEditing(created);setCreating(false);setTab('All Pages');setPageTitle('')
   },'Draft created. Add property details before publishing.');return
  }
  await action(async()=>{
   const created=await api<Editorial>('/api/admin/pages',{method:'POST',body:JSON.stringify({title:pageTitle.trim(),template_id:Number(pageTemplate)})})
   setEditEditorial(created);setTab('All Pages');setPageTitle('')
  },'Editorial draft created.')
 }
 const openTemplate=(t:AccomTemplate)=>{setSelectedTemplate(t);setMappingFields(t.fields.map(f=>({...f})));apiText('/api/admin/templates/'+t.id+'/preview').then(setPreviewHTML).catch(report)}
 const upload=async()=>{
  if(!file)return setError('Choose an HTML file, project ZIP or page component.')
  setBusy(true);setError('');setInspection(null);setSelectedSource('')
  try{
   const body=new FormData();body.append('file',file)
   if(/\\.html?$/i.test(file.name)){
     body.append('name',templateName||file.name.replace(/\\.html?$/i,''))
     const t=await api<AccomTemplate>('/api/admin/templates',{method:'POST',body})
     await refresh();openTemplate(t)
     setNotice('HTML imported. Review detected sections and fields before approval.')
   }else{
     const result=await api<ProjectInspection>('/api/admin/projects/inspect',{method:'POST',body})
     setInspection(result)
     setSelectedSource(result.pages.find(p=>p.renderable_html)?.file||result.pages[0]?.file||'')
     setNotice('Project scanned safely. Review the discovered pages and choose a built HTML page to import.')
   }
  }catch(e){report(e)}finally{setBusy(false)}
 }
 const importSelectedSource=async()=>{
  if(!file||!selectedSource)return
  setBusy(true);setError('')
  try{
   const body=new FormData();body.append('file',file);body.append('source_path',selectedSource);body.append('name',templateName||selectedSource.split('/').pop()?.replace(/\\.html?$/i,'')||'Imported page')
   const t=await api<AccomTemplate>('/api/admin/templates/import-project',{method:'POST',body})
   await refresh();openTemplate(t);setInspection(null);setNotice('Built HTML page imported. Review content mapping before approval.')
  }catch(e){report(e)}finally{setBusy(false)}
 }
 const saveMapping=async()=>{if(!selectedTemplate)return;await action(async()=>{const t=await api<AccomTemplate>('/api/admin/templates/'+selectedTemplate.id,{method:'PATCH',body:JSON.stringify({fields:mappingFields,approved:true})});openTemplate(t)},'Template mapping approved')}
 const updateEnquiry=async(id:number,changes:Record<string,unknown>)=>{
  if(changes.status==='booked'){
   if(user.role!=='admin')return setError('Only administrators can confirm bookings')
   const ref=window.prompt('Provider booking reference (required to confirm):')
   if(!ref?.trim())return
   changes.booking_reference=ref.trim()
  }
  await action(()=>api('/api/admin/enquiries/'+id,{method:'PATCH',body:JSON.stringify(changes)}),'Enquiry updated')
 }
 const openNotes=async(id:number)=>{setSelectedEnquiry(id);setNoteText('');try{setNotes(await api<typeof notes>('/api/admin/enquiries/'+id+'/notes'))}catch(e){report(e)}}
 const addNote=async()=>{if(!selectedEnquiry||!noteText.trim())return;await action(async()=>{await api('/api/admin/enquiries/'+selectedEnquiry+'/notes',{method:'POST',body:JSON.stringify({message:noteText})});setNotes(await api<typeof notes>('/api/admin/enquiries/'+selectedEnquiry+'/notes'));setNoteText('')},'Note saved')}
 const changeCashback=async(c:CashbackRow,status:string)=>{await action(()=>api('/api/admin/cashback/'+c.id,{method:'PATCH',body:JSON.stringify({...c,status})}),'Cashback updated')}
 return <main className="category-shell">
  <aside className="category-sidebar"><div className="category-sidebar-brand"><Logo/><small>CONTENT MANAGER</small></div><nav aria-label="Admin navigation"><div className="category-sidebar-item active">Category</div></nav><div className="category-sidebar-spacer"/><div className="admin-side-bottom"><strong>Content workspace</strong><small>{user.role==='admin'?'Administrator':'Content editor'}</small></div><button className="category-exit" onClick={()=>go('/')}>View website <ArrowRight size={14}/></button><button className="category-exit" onClick={()=>{token='';sessionStorage.removeItem('accom_token');window.location.href='/login'}}>Sign out <ArrowRight size={14}/></button></aside>
  <div className="category-content"><div className="category-heading"><h1>Category</h1><div className="category-heading-actions"><button type="button" className="category-tools-trigger" onClick={()=>setShowOperations(true)}>Operations</button><span className="signed-user">{user.name}</span></div></div>
  <nav className="category-tabs" role="tablist" aria-label="Category tabs">{(['All Pages','Add Page','Upload Template'] as const).map(t=><button key={t} type="button" className={tab===t?'active':''} aria-selected={tab===t} role="tab" onClick={()=>{setTab(t);setError('');setNotice('')}}>{t}</button>)}</nav>
    {error&&<div className="error admin-message" role="alert">{error}<button onClick={()=>setError('')} aria-label="Dismiss error">×</button></div>}
  {notice&&<div className="notice admin-message" role="status">{notice}<button onClick={()=>setNotice('')} aria-label="Dismiss message">×</button></div>}
  {tab==='All Pages'&&<>
    <div className="category-list-toolbar" role="search">
      <div className="category-filters" role="group" aria-label="Page publishing status">{(['All','Published','Draft'] as const).map(t=><button key={t} type="button" aria-pressed={filter===t} className={filter===t?'selected':''} onClick={()=>setFilter(t)}>{t}<small>{t==='All'?[...properties.filter(p=>!p.is_demo),...pages].filter(p=>!p.archived).length:t==='Published'?[...properties.filter(p=>!p.is_demo),...pages].filter(p=>p.published&&!p.archived).length:[...properties.filter(p=>!p.is_demo),...pages].filter(p=>!p.published&&!p.archived).length}</small></button>)}</div>
      <div className="category-search"><Search size={16}/><input aria-label="Search pages" type="search" placeholder="Search pages…" value={search} onChange={e=>setSearch(e.target.value)}/></div>
    </div>
    <div className="category-table-wrap">
      <div className="category-table-header" aria-hidden="true"><span>#</span><span>Page Name</span><span>Template</span><span>URL</span><span>Status</span><span>Last updated</span><span>Actions</span></div>
      <div className="category-page-list">
      {filtered.map((p,i)=><article key={p.kind+'-'+p.id} className="category-page-row">
        <span className="category-table-number">{String(i+1).padStart(2,'0')}</span>
        <div className="category-table-name"><h3>{p.title}</h3><small>{p.kind==='property'?'Student accommodation':'Editorial page'}</small></div>
        <span className="category-table-type">{p.kind==='property'?'Accom Property Detail':(templates.find(t=>t.id===(p as Editorial).template_id)?.name||'Imported template')}</span>
        <span className="category-table-url" title={'/'+p.slug+'/'}>/{p.slug}/</span>
        <span className={'category-page-status '+(p.archived?'archived':p.published?'published':'draft')}>{p.archived?'Archived':p.published?'Published':'Draft'}</span>
        <span className="category-table-date">{p.kind==='property'&&p.verified_at?fmt(p.verified_at):'—'}</span>
        <div className="category-page-actions">
          <details className="category-row-action-menu"><summary>Actions <ChevronDown size={14}/></summary><div className="category-row-action-dropdown">
            {(user.role!=='editor'||!p.published)&&<button type="button" onClick={e=>{e.currentTarget.closest('details')?.removeAttribute('open');p.kind==='property'?startEdit(p as Property):setEditEditorial(p as Editorial)}}>Edit page</button>}
            {p.kind==='property'&&(!p.published||user.role==='admin')&&<button type="button" onClick={()=>{setRoomParent(p as Property);setRoom(null)}}>Manage rooms</button>}
            <button type="button" onClick={()=>{if(p.kind==='property'){const w=window.open('about:blank','_blank');api<{url:string}>('/api/admin/properties/'+p.id+'/preview-link',{method:'POST'}).then(v=>{if(w)w.location.href=v.url;else window.location.href=v.url}).catch(e=>{w?.close();report(e)})}else{apiText('/api/admin/pages/'+p.id+'/preview').then(setPreviewHTML).catch(report);setSelectedTemplate(null)}}}>Preview</button>
            {user.role==='admin'&&!p.published&&!p.archived&&<button type="button" onClick={()=>action(()=>api('/api/admin/'+(p.kind==='property'?'properties':'pages')+'/'+p.id+'/publish',{method:'POST'}),'Page published')}>Publish</button>}
            {user.role==='admin'&&p.kind==='property'&&<button type="button" onClick={()=>{if(window.confirm(p.archived?'Restore this page?':'Archive this page?'))action(()=>api('/api/admin/properties/'+p.id+'/'+(p.archived?'restore':'archive'),{method:'POST'}),p.archived?'Restored':'Archived')}}>{p.archived?'Restore page':'Archive page'}</button>}
          </div></details>
        </div>
      </article>)}
      {!filtered.length&&<div className="category-empty"><strong>No pages here yet.</strong><p>Create your first property page or import a template to get started.</p><button type="button" className="primary" onClick={()=>setTab('Add Page')}>Add a page <ArrowRight size={15}/></button></div>}
      </div>
    </div>
    {[...properties.filter(p=>!p.is_demo),...pages].some(p=>p.archived)&&<button type="button" className="category-archived-link" onClick={()=>setFilter(cur=>cur==='Archived'?'All':'Archived')}>{filter==='Archived'?'← Back to active pages':'View archived pages'}</button>}
  </>}
  {tab==='Add Page'&&<section className="category-split-workspace category-add-page">
    <div className="category-form-card category-add-form">
      <h2>Add Page</h2>
      <form className="category-create-form" onSubmit={e=>{e.preventDefault();void create()}}>
        <label>Template<select aria-label="Template" value={pageTemplate} onChange={e=>setPageTemplate(e.target.value)}>
          <option value="native-property">Accom Property Detail — Approved original</option>
          {templates.filter(t=>t.approved).map(t=><option key={t.id} value={t.id}>{t.name}</option>)}
        </select></label>
        <label>Page name<input aria-label="Page name" required minLength={3} maxLength={220} placeholder="e.g. iQ Kingston Student Residence" value={pageTitle} onChange={e=>setPageTitle(e.target.value)}/></label>
        <p className="category-title-guidance">Use the property or page name students will recognize. You can edit the SEO title separately.</p>
        <button type="submit" className="primary category-submit" disabled={busy}>Create page <ArrowRight size={17}/></button>
      </form>
    </div>
    <div className="category-template-preview-pane">
      <div className="category-preview-pane-heading"><h3>Template Preview</h3><button type="button" className="outline" onClick={()=>{if(pageTemplate==='native-property')setShowApprovedDesign(true);else if(addTemplatePreview){setPreviewHTML(addTemplatePreview);setSelectedTemplate(null)}}}>Expand <ArrowRight size={16}/></button></div>
      <div className="category-frame-shell" ref={templateFrameContainer}>
        <div className="category-frame-scaled" style={{width:1280*templateFrameScale,height:960*templateFrameScale}}>
        {pageTemplate==='native-property'?<iframe title="Approved Accom template preview" src="/accom-live/index.html" sandbox="allow-scripts allow-popups" style={{width:1280,height:960,transform:'scale('+templateFrameScale+')',transformOrigin:'top left'}}/>:
         addTemplatePreview?<iframe title="Selected editorial template preview" sandbox="" srcDoc={addTemplatePreview} style={{width:1280,height:960,transform:'scale('+templateFrameScale+')',transformOrigin:'top left'}}/>:
         <div className="category-preview-pending">Choose an approved template to see its preview.</div>}
        </div>
      </div>
      <p className="category-preview-helper">{pageTemplate==='native-property'?'This is the exact original live-page design. The template stays visually unchanged while content fields are mapped.':'Safe visual preview of the approved content template.'}</p>
    </div>
  </section>}
  {tab==='Upload Template'&&<section className="category-template-workspace">
    <div className="category-split-workspace category-import-workspace">
      <div className="category-form-card category-import-form">
        <h2>Upload Template</h2>
        <p className="category-import-subtitle">Bring in your project page, then review the detected content.</p>
        <div className="category-upload-card">
          <label className="category-upload-drop">
            <span className="category-upload-glyph"><Upload size={25}/></span>
            <strong>{file?'File selected':'Drop a project file here'}</strong>
            <span className="category-file-button">{file?'Choose another':'Choose file'}</span>
            <input type="file" accept=".html,.htm,.zip,.jsx,.tsx,.vue,.svelte,.astro" onChange={e=>{setFile(e.target.files?.[0]||null);setInspection(null);setSelectedSource('');setSelectedTemplate(null)}}/>
            <small>{file?.name||'HTML up to 1.5 MB · project ZIP up to 24 MB · JSX / TSX / Vue / Astro'}</small>
          </label>
          <label>Template name (optional)<input value={templateName} onChange={e=>setTemplateName(e.target.value)} placeholder="e.g. Student residence detail"/></label>
          <button type="button" className="primary category-submit" disabled={busy||user.role!=='admin'||!file} onClick={upload}>{busy?'Inspecting…':'Inspect project'} <ArrowRight size={16}/></button>
        </div>
        <div className="category-upload-help"><strong>How page extraction works</strong><p>Upload your React, Next.js, Vite or other source as a ZIP to detect routes, headings, CTAs and image references. For a pixel-matched visual template, include a built static HTML export. Source code is never executed on the server.</p></div>
      </div>
      <div className="category-template-preview-pane">
        <div className="category-preview-pane-heading"><h3>Template Inspection</h3><span className="category-light-status">{inspection?'Project inspected':selectedTemplate?'Mapped template':'Ready to inspect'}</span></div>
        <div className="category-frame-shell" ref={templateFrameContainer}>
         <div className="category-frame-scaled" style={{width:1280*templateFrameScale,height:960*templateFrameScale}}>
         {inspection?<div className="category-source-preview-message"><ImageIcon size={31}/><strong>{inspection.pages.length} routes or components detected</strong><p>Select a route in the inspection panel below. A pixel-accurate live preview needs a static build/export and its assets.</p></div>:
          selectedTemplate&&previewHTML?<iframe title="Imported template preview" srcDoc={previewHTML} sandbox="" style={{width:1280,height:960,transform:'scale('+templateFrameScale+')',transformOrigin:'top left'}}/>:
          <iframe title="Original Accom template inspection" src="/accom-live/index.html" sandbox="allow-scripts allow-popups" style={{width:1280,height:960,transform:'scale('+templateFrameScale+')',transformOrigin:'top left'}}/>}
         </div>
        </div>
        <p className="category-preview-helper">Original Accom template reference. Imported project fields and pages appear below after inspection.</p>
      </div>
    </div>
    {inspection&&<section className="category-project-results">
      <div className="category-detection-header"><div><span className="eyebrow">PROJECT DISCOVERY</span><h3>{inspection.filename}</h3><p>{inspection.framework} · {inspection.pages.length} page candidates · {inspection.total_fields} text and media candidates</p></div></div>
      <div className="category-project-content">
        <div className="category-project-routes"><h4>Detected routes & components</h4>{inspection.pages.map(p=><button key={p.file} type="button" className={selectedSource===p.file?'selected':''} onClick={()=>setSelectedSource(p.file)}><strong>{p.route}</strong><span>{p.file}</span><small>{p.renderable_html?'HTML ready for mapping':'Source · build required'}</small></button>)}</div>
        <div className="category-project-fields">{inspection.pages.filter(p=>p.file===selectedSource).map(p=><div key={p.file}><h4>{p.route==='(component)'?p.file:p.route}</h4><p>{p.type} · {p.fields.length} detected fields</p><div className="category-project-field-list">{p.fields.length?p.fields.map((field,i)=><div key={i}><span>{field.kind}{field.tag?' · '+field.tag:''}</span><strong>{field.value}</strong></div>):<p>No static fields found. Dynamic content may be loaded at runtime.</p>}</div>{p.renderable_html&&file?.name.endsWith('.zip')?<button type="button" className="primary" disabled={busy} onClick={importSelectedSource}>Import this HTML page <ArrowRight size={15}/></button>:<div className="category-project-note"><strong>Build/export required for visual editing.</strong><p>The source was analyzed, but it cannot be rendered as the original site without its compiled assets and runtime. {inspection.recommended_build_command} and upload the output ZIP.</p></div>}</div>)}</div>
      </div>
    </section>}
    <div className="accom-native-template-card"><div><strong>Approved Accom master template</strong><p>Keep the complete original page available as the design reference while importing additional pages.</p></div><button type="button" className="outline" onClick={()=>setShowApprovedDesign(true)}>View original <ArrowRight size={15}/></button></div>
    {!!templates.length&&<div className="category-template-library"><div className="category-subheading"><h3>Uploaded templates</h3><span>{templates.length} total</span></div><div className="category-template-list">{templates.map(t=><button key={t.id} type="button" className={selectedTemplate?.id===t.id?'selected':''} aria-pressed={selectedTemplate?.id===t.id} onClick={()=>openTemplate(t)}><strong>{t.name}</strong><small>{t.sections.length} sections · {t.fields.length} fields · {t.approved?'Approved':'Needs review'}</small></button>)}</div></div>}
   {selectedTemplate&&<div className="category-detection-results">
    <div className="category-detection-header"><div><span className="eyebrow">DETECTION RESULTS</span><h3>{selectedTemplate.name}</h3><p>Inspect all detected sections, field types, original values and edit permissions.</p></div><div className="category-detection-metrics"><div><strong>{selectedTemplate.sections.length}</strong><span>Sections</span></div><div><strong>{mappingFields.length}</strong><span>Fields</span></div><div><strong>{mappingFields.filter(f=>f.mode==='page').length}</strong><span>Editable</span></div></div></div>
    <div className="category-detection-layout">
     <div className="category-detection-map"><div className="category-map-topbar"><h4>Detected sections</h4><span>{selectedTemplate.sections.length} mapped</span></div>
      {selectedTemplate.sections.map((sec,i)=>{const fields=mappingFields.filter(f=>f.section_id===sec.id);return <details className="category-map-section" key={sec.id} open>
       <summary><span className="category-section-number">{String(i+1).padStart(2,'0')}</span><span className="category-section-title">{sec.name}<small>{sec.id}</small></span><span className="category-section-count">{fields.length} {fields.length===1?'field':'fields'}</span><ChevronDown size={16}/></summary>
       {fields.length?<div className="category-map-fields"><div className="category-map-column-head"><span>Field name</span><span>Detected content / type</span><span>Editing</span></div>{fields.map(f=><div className="category-map-field" key={f.key}>
         <label><span className="sr-only">Field name</span><input aria-label={'Field name for '+f.key} value={f.label} onChange={e=>setMappingFields(prev=>prev.map(x=>x.key===f.key?{...x,label:e.target.value}:x))}/></label>
         <div className="category-field-info"><span>{f.kind} · {f.tag||'element'}</span><small title={f.default}>{f.default?.trim()||'No default value'}</small></div>
         <label><span className="sr-only">Edit permissions</span><select aria-label={'Editing mode for '+f.key} value={f.mode} onChange={e=>setMappingFields(prev=>prev.map(x=>x.key===f.key?{...x,mode:e.target.value as 'static'|'page'}:x))}><option value="page">Editable</option><option value="static">Static</option></select></label>
       </div>)}</div>:<p className="category-no-fields">No editable content detected in this section.</p>}
      </details>})}
      <div className="category-map-footer"><span>{selectedTemplate.approved?'Approved template · update its mapping below':'Review before approval.'}</span>{user.role==='admin'&&<button type="button" className="primary" disabled={busy} onClick={saveMapping}>Save & approve</button>}</div>
     </div>
     <aside className="category-detection-preview"><div className="category-preview-title"><h4>Visual preview</h4><p>Sanitized HTML from the selected template</p></div><iframe title={'Preview of '+selectedTemplate.name} className="category-preview-frame" sandbox="" srcDoc={previewHTML}/></aside>
    </div>
   </div>}
  </section>}
  </div>
  {showOperations&&<div className="category-ops-overlay" role="presentation" onMouseDown={e=>{if(e.target===e.currentTarget)setShowOperations(false)}}>
    <section className="category-ops-dialog" role="dialog" aria-modal="true" aria-label="Student operations and team access">
     <header className="category-ops-dialog-head"><div><span className="eyebrow">CATEGORY / OPERATIONS</span><h2>Operations</h2><p>Manage enquiries, cashback and staff without adding sidebar modules.</p></div><button type="button" className="outline tiny" onClick={()=>setShowOperations(false)}>Close <X size={17}/></button></header>
     <div className="category-ops-dialog-body">
    <details className="category-operations"><summary>Student enquiries <span>{enquiries.length}</span></summary><div className="category-operations-inner">{enquiries.map(e=><div className="category-lead" key={e.id}><div><strong>{e.name}</strong><small>{e.email} · {e.property}</small><p>{e.message||'No message'} </p></div><select aria-label={'Status for '+e.name} value={e.status} onChange={x=>updateEnquiry(e.id,{status:x.target.value})}>{['new','contacted','in_progress','applied',...(user.role==='admin'?['booked']:[]),'closed'].map(s=><option key={s} value={s}>{s.replace('_',' ')}</option>)}</select><select aria-label={'Consultant for '+e.name} value={e.assigned_to_id??''} onChange={x=>updateEnquiry(e.id,{assigned_to_id:x.target.value?Number(x.target.value):null})}><option value="">Unassigned</option>{staff.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select><button className="outline tiny" onClick={()=>openNotes(e.id)}>Notes</button></div>)}{!enquiries.length&&<p>No enquiries yet.</p>}</div></details>
    <details className="category-operations"><summary>Cashback records <span>{cashback.length}</span></summary><div className="category-operations-inner">{user.role==='admin'&&<form className="cashback-form" onSubmit={async e=>{e.preventDefault();const f=new FormData(e.currentTarget);await action(()=>api('/api/admin/cashback',{method:'POST',body:JSON.stringify({enquiry_id:Number(f.get('enquiry_id')),amount:f.get('amount')?Number(f.get('amount')):null,currency:'GBP',status:'under_review'})}),'Cashback record created')}}><label>Enquiry<select name="enquiry_id" required><option value="">Select enquiry</option>{enquiries.filter(e=>!cashback.some(c=>c.enquiry_id===e.id)).map(e=><option key={e.id} value={e.id}>{e.name} · {e.property}</option>)}</select></label><label>Amount<input name="amount" type="number" min="0" step=".01"/></label><button className="primary" type="submit">Create record</button></form>}{cashback.map(c=><div className="category-cashback" key={c.id}><strong>Enquiry #{c.enquiry_id}</strong><span>{c.amount===null?'Amount pending':money(c.amount,c.currency,'week').split('/')[0]}</span><select value={c.status} disabled={user.role!=='admin'} onChange={e=>changeCashback(c,e.target.value)}>{['under_review','eligible','approved','paid','ineligible'].map(s=><option key={s} value={s}>{s.replace('_',' ')}</option>)}</select></div>)}</div></details>
    {user.role==='admin'&&<details className="category-operations"><summary>Team access and audit trail</summary><div className="category-operations-inner"><div className="category-staff">{staff.map(s=><div key={s.id}><strong>{s.name}</strong><small>{s.email} · {s.role}</small>{s.id!==user.id&&<button className="outline tiny" onClick={()=>action(()=>api('/api/admin/staff/'+s.id,{method:'PATCH',body:JSON.stringify({active:false})}),'Staff access revoked')}>Deactivate</button>}</div>)}</div><form className="category-staff-create" onSubmit={async e=>{e.preventDefault();await action(()=>api('/api/admin/staff',{method:'POST',body:JSON.stringify({name:staffName,email:staffEmail,username:staffUsername||null,password:staffPassword,role:'editor'})}),'Editor created');setStaffName('');setStaffEmail('');setStaffUsername('');setStaffPassword('')}}><h3>Add editor</h3><label>Name<input required value={staffName} onChange={e=>setStaffName(e.target.value)}/></label><label>Email<input type="email" required value={staffEmail} onChange={e=>setStaffEmail(e.target.value)}/></label><label>Username (optional)<input type="text" value={staffUsername} onChange={e=>setStaffUsername(e.target.value)} placeholder="e.g. editor.jane" minLength={3} maxLength={32}/></label><label>Temporary password (minimum 12 characters)<input type="password" minLength={12} required value={staffPassword} onChange={e=>setStaffPassword(e.target.value)}/></label><button className="primary">Create editor</button></form><h3>Recent changes</h3>{audit.slice(0,15).map((a,i)=><p key={i} className="audit-entry">{a.actor}: {a.event} #{a.reference} · {fmt(a.at)}</p>)}</div></details>}

     </div>
    </section>
   </div>}
  {(editing||creating)&&<PropertyEditor source={editing} close={()=>{setEditing(null);setCreating(false)}} saved={()=>{refresh();setEditing(null);setCreating(false);setTab('All Pages');setNotice('Property saved as draft')}} editRoom={chosen=>{if(!editing)return;setEditing(null);setRoomParent(editing);setRoom(chosen)}}/>}
  {roomParent&&<RoomManager p={roomParent} close={()=>setRoomParent(null)} saved={()=>{refresh();setRoomParent(null);setNotice('Room changes saved')}} current={room} setCurrent={setRoom}/>}
  {showApprovedDesign&&<div className="category-preview-overlay accom-original-source-modal" role="dialog" aria-modal="true" aria-label="Approved Accom source design"><div className="category-preview-bar"><div><strong>Approved Accom property design</strong><small>Exact deployed page · 13 sections · interactive reference · no real enquiries are submitted</small></div><button type="button" className="outline tiny" onClick={()=>setShowApprovedDesign(false)}>Back to Category <X size={15}/></button></div><iframe className="accom-original-page-frame" title="Complete original Accom property page" src="/accom-live/index.html" sandbox="allow-scripts allow-popups"/></div>}
  {preview&&<div className="category-preview-overlay"><div className="category-preview-bar"><strong>Preview · {preview.name} {preview.published?'':'(Draft)'}</strong><button className="outline tiny" onClick={()=>setPreview(null)}>Close preview <X size={15}/></button></div><div className="category-preview-scroll"><Listing slug={preview.slug} go={go} user={user} previewData={preview}/></div></div>}
  {previewHTML&&!selectedTemplate&&<div className="category-preview-overlay"><div className="category-preview-bar"><strong>Editorial page preview</strong><button className="outline tiny" onClick={()=>setPreviewHTML('')}>Close <X size={15}/></button></div><iframe title="Editorial page preview" sandbox="" className="category-preview-full" srcDoc={previewHTML}/></div>}
  {editEditorial&&<EditorialEditor page={editEditorial} templates={templates} close={()=>setEditEditorial(null)} onSaved={async()=>{await refresh();setEditEditorial(null);setNotice('Page saved')}}/>}
  {selectedEnquiry!==null&&<div className="drawer-shade"><div className="drawer category-notes"><div className="drawer-header"><h2>Enquiry #{selectedEnquiry} · Notes</h2><button onClick={()=>setSelectedEnquiry(null)} aria-label="Close notes"><X/></button></div><div className="category-notes-body">{notes.map(n=><div key={n.id} className="note-card"><strong>{n.by}</strong><p>{n.message}</p><small>{fmt(n.created_at)}</small></div>)}{!notes.length&&<p>No notes added yet.</p>}<textarea aria-label="Consultant note" rows={4} value={noteText} onChange={e=>setNoteText(e.target.value)}/><button className="primary" onClick={addNote} disabled={!noteText.trim()}>Add note</button></div></div></div>}
 </main>
}
async function apiText(path:string):Promise<string>{const response=await fetch(path,{headers:token?{Authorization:'Bearer '+token}:{}});if(!response.ok)throw new Error('Preview unavailable ('+response.status+')');return response.text()}
function EditorialEditor({page,templates,close,onSaved}:{page:Editorial;templates:AccomTemplate[];close:()=>void;onSaved:()=>void}){
 const [form,setForm]=useState(page),[busy,setBusy]=useState(false),[error,setError]=useState('')
 const template=templates.find(t=>t.id===page.template_id)
 const update=(key:string,value:string)=>setForm(f=>({...f,values:{...f.values,[key]:value}}))
 const save=async(e:React.FormEvent)=>{e.preventDefault();setBusy(true);setError('');try{await api('/api/admin/pages/'+page.id,{method:'PATCH',body:JSON.stringify(form)});onSaved()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <div className="drawer-shade"><div className="drawer"><div className="drawer-header"><div><span className="eyebrow">EDITORIAL PAGE</span><h2>{page.title}</h2></div><button onClick={close} aria-label="Close editor"><X/></button></div><form onSubmit={save} className="drawer-form"><label>Title<input value={form.title} onChange={e=>setForm(f=>({...f,title:e.target.value}))}/></label>{template?.sections.map(section=><details open key={section.id} className="category-map-section"><summary>{section.name}</summary>{template.fields.filter(f=>f.section_id===section.id&&f.mode==='page').map(f=><label key={f.key}>{f.label}<textarea rows={f.kind==='text'?2:1} value={form.values[f.key]??f.default} onChange={e=>update(f.key,e.target.value)}/></label>)}</details>)}<label>SEO title<input value={form.seo_title} onChange={e=>setForm(f=>({...f,seo_title:e.target.value}))}/></label><label>Meta description<textarea rows={2} value={form.meta_description} onChange={e=>setForm(f=>({...f,meta_description:e.target.value}))}/></label><label className="checkline"><input type="checkbox" checked={form.noindex} onChange={e=>setForm(f=>({...f,noindex:e.target.checked}))}/> Noindex</label>{error&&<p className="error">{error}</p>}<div className="drawer-footer"><button type="button" className="outline" onClick={close}>Cancel</button><button className="primary" disabled={busy}>Save page</button></div></form></div></div>
}

const MASTER_PREVIEW_SELECTOR:Record<string,string> = {
 top:'#property-identity', gallery:'section.gallery', overview:'#overview', about:'#about', tours:'#tours',
 amenities:'#amenities', rooms:'#rooms', rules:'#rules', payments:'#payments',
 floorplan:'#floorplan', neighbourhood:'#neighbourhood', faqs:'#faqs',
 location:'#location', reviews:'#reviews', enquiry:'.cta-aside',
}

function PropertyEditor({source,close,saved,editRoom}:{source:Property|null;close:()=>void;saved:()=>void;editRoom:(room:Room|null)=>void}){
 const [form,setForm]=useState({...defaults,...(source||{}),gallery:(source?.gallery||[]).map((photo,i):Media=>({...photo,layout:photo.layout||(i===0?'large':'regular')}))})
 const [busy,setBusy]=useState(false),[error,setError]=useState('')
 const [activeSection,setActiveSection]=useState('top')
 const [seoOpen,setSeoOpen]=useState(false)
 const [contentSections,setContentSections]=useState<MasterSection[]>([])
 const [contentError,setContentError]=useState('')
 const [templateSample,setTemplateSample]=useState<Record<string,unknown>|null>(null)
 const [usingTemplateSample,setUsingTemplateSample]=useState(false)
 const [previewHtml,setPreviewHtml]=useState('')
 const [previewLoading,setPreviewLoading]=useState(false)
 const [previewError,setPreviewError]=useState('')
 const [previewMode,setPreviewMode]=useState<'desktop'|'mobile'>('desktop')
 const [sourceReference,setSourceReference]=useState(false)
 const [sourceSection,setSourceSection]=useState('top')
 const [previewScale,setPreviewScale]=useState(.4)
 const previewContainerRef=useRef<HTMLDivElement|null>(null)
 const previewFrameRef=useRef<HTMLIFrameElement|null>(null)
 const fieldsPanelRef=useRef<HTMLElement|null>(null)
 const original=JSON.stringify({...defaults,...(source||{})})
 const [saveNotice,setSaveNotice]=useState('')
 const dirty=JSON.stringify({...defaults,...(source||{}),...form})!==original
 const safeClose=()=>{if(!dirty||window.confirm('Discard your unsaved changes?'))close()}
 function set<K extends keyof typeof defaults>(key:K,value:(typeof defaults)[K]){setForm(f=>({...f,[key]:value}));setSaveNotice('')}
 const media=(item:Media,change:(v:Media)=>void,group:string)=> <div className="repeater-photo-fields">
   <label>Image URL<input placeholder="https://example.com/photo.webp or upload below" value={item.url} onChange={e=>change({...item,url:e.target.value})}/></label><label>Or upload a photo (JPG, PNG, WebP)<input type="file" accept="image/jpeg,image/png,image/webp" onChange={async e=>{const f=e.target.files?.[0];if(!f)return;try{const url=await uploadPhoto(f);change({...item,url})}catch(err){setError((err as Error).message)}}}/></label>
   <label>Alt text<input placeholder="Describe the actual image" value={item.alt||''} onChange={e=>change({...item,alt:e.target.value})}/></label>
   <label>Category<input placeholder="Rooms / Exterior / Shared spaces" value={item.category||''} onChange={e=>change({...item,category:e.target.value})}/></label>
   <fieldset className="image-layout-switch"><legend>Picture size on the listing</legend><div className="layout-switch" role="group" aria-label={`${group} picture layout`}>
    {(['regular','large'] as const).map(v=><button key={v} type="button" aria-pressed={(item.layout||'regular')===v} className={(item.layout||'regular')===v?'selected':''} onClick={()=>change({...item,layout:v})}>{v==='regular'?'Regular':'Large'}</button>)}
   </div><small>Regular: one grid cell. Large: a prominent two-by-two tile.</small></fieldset>
   <div className={'image-live-preview '+(item.layout==='large'?'large':'regular')}>{absolute(item.url)?<img src={item.url} alt={item.alt||'Image layout preview'} loading="lazy"/>:<span>Enter a valid image URL to preview</span>}</div>
 </div>
 const submit=async(e:React.FormEvent)=>{
  e.preventDefault()
  if(form.name.trim().length<3||form.city.trim().length<2){
   setActiveSection('top')
   fieldsPanelRef.current?.scrollTo({top:0,behavior:'instant'})
   setError('Complete the property name and city in Hero & gallery before saving.')
   return
  }
  setBusy(true);setError('');setSaveNotice('');
  const trimmed=(s:string)=>s.trim()
  const data={...form,
   highlights:form.highlights.map(trimmed).filter(Boolean),highlight_descriptions:form.highlights.map((_,i)=>trimmed(form.highlight_descriptions[i]||'')),amenities:form.amenities.map(trimmed).filter(Boolean),
   gallery:form.gallery.filter(p=>p.url.trim()).map(p=>({...p,url:p.url.trim(),alt:p.alt?.trim()||form.name+' accommodation photo',layout:p.layout||'regular'})),
   floorplans:form.floorplans.filter(p=>p.url.trim()).map(p=>({...p,url:p.url.trim(),alt:p.alt?.trim()||'Floor plan',layout:p.layout||'regular'})),
   faq:form.faq.filter(p=>p.question.trim()||p.answer.trim()),policies:form.policies.filter(p=>p.question.trim()||p.answer.trim()),
   landmarks:form.landmarks.filter(p=>p.name.trim()||p.detail.trim()),offers:form.offers.filter(p=>p.title.trim()||p.description.trim()),
   reviews:form.reviews.filter(p=>p.name.trim()||p.quote.trim())}
  try{await api(source?'/api/admin/properties/'+source.id:'/api/admin/properties',{method:source?'PATCH':'POST',body:JSON.stringify(data)});saved()}
  catch(err){setError((err as Error).message)}finally{setBusy(false)}
 }

 useEffect(()=>{
  const query=window.matchMedia('(max-width:620px)')
  const update=()=>{if(query.matches)setPreviewMode('mobile')}
  update()
  query.addEventListener('change',update)
  return()=>query.removeEventListener('change',update)
 },[])
 const sourceSections=[
  {id:'top',name:'Hero & gallery'},
  {id:'overview',name:'Residence overview'},
  {id:'about',name:'Property details'},
  {id:'tours',name:'Photo categories & tour'},
  {id:'amenities',name:'Amenities & bills'},
  {id:'rooms',name:'Rooms & price choices'},
  {id:'rules',name:'House rules'},
  {id:'payments',name:'Payments & fees'},
  {id:'floorplan',name:'Floor plans'},
  {id:'neighbourhood',name:'Neighbourhood'},
  {id:'faqs',name:'FAQs'},
  {id:'location',name:'Landmarks & location'},
  {id:'reviews',name:'Student reviews'}
 ]
 const jumpSource=(id:string)=>{
  setSourceSection(id)
  previewFrameRef.current?.contentWindow?.postMessage({type:'accom-open-section',id},'*')
 }
 const sections=[
  {id:'top',title:'Property identity',desc:'Property name, address and university',index:'01',icon:Home},
  {id:'gallery',title:'Photo gallery',desc:'Hero gallery images, captions and layout',index:'02',icon:ImageIcon},
  {id:'overview',title:'Residence overview',desc:'Introductory description and highlight cards',index:'03',icon:LayoutDashboard},
  {id:'about',title:'Living experience',desc:'Property story and room-type explanation',index:'04',icon:Sparkles},
  {id:'tours',title:'Photos & virtual tours',desc:'Photo categories and tour information',index:'05',icon:ImageIcon},
  {id:'amenities',title:'Amenities & bills',desc:'Included facilities and bills explanation',index:'06',icon:Check},
  {id:'rooms',title:'Rooms & tenancy plans',desc:'Room types, pricing and availability',index:'07',icon:LayoutDashboard},
  {id:'rules',title:'House rules',desc:'Policies, cancellations and visitor rules',index:'08',icon:ShieldCheck},
  {id:'payments',title:'Payments & fees',desc:'Payment information, fees and offers',index:'09',icon:Wallet},
  {id:'floorplan',title:'Floor plans',desc:'Plan images and viewing requests',index:'10',icon:ImageIcon},
  {id:'neighbourhood',title:'Neighbourhood',desc:'Surrounding area and locality photo',index:'11',icon:MapPin},
  {id:'faqs',title:'Frequently asked questions',desc:'Resident questions with individual answers',index:'12',icon:Search},
  {id:'location',title:'Location & landmarks',desc:'Landmarks and route information',index:'13',icon:Compass},
  {id:'reviews',title:'Student reviews',desc:'Verified review content and attribution',index:'14',icon:Heart},
  {id:'enquiry',title:'Enquiry & CTA panel',desc:'Sticky side panel and enquiry buttons',index:'15',icon:ArrowRight},
 ]
 const currentSection=sections.find(item=>item.id===activeSection)||sections[0]
 const copyFields=contentSections.find(section=>section.id===activeSection)?.fields||[]
 const copyGroups=[...new Set(copyFields.map(field=>field.group))].map(name=>({name,fields:copyFields.filter(field=>field.group===name)}))
 const applyTemplateSample=(sample:Record<string,unknown>)=>{
  setForm(previous=>{
   const updated={...previous}
   for(const key of ['city','country','postcode','university','address','description','gallery','highlights','highlight_descriptions','amenities','policies','faq','landmarks'] as const){
    const current=updated[key]
    const next=sample[key]
    if((typeof current==='string'&&!current.trim()&&typeof next==='string'&&next.trim()) ||
       (Array.isArray(current)&&current.length===0&&Array.isArray(next)&&next.length>0)){
     ;(updated as Record<string,unknown>)[key]=next
    }
   }
   return {...updated,is_demo:true,noindex:true}
  })
  setUsingTemplateSample(true)
  setSaveNotice('')
 }
 useEffect(()=>{
  if(!source?.id)return
  let alive=true
  setContentError('')
  api<{sections:MasterSection[];template_sample:Record<string,unknown>|null;auto_prefill_template:boolean}>('/api/admin/properties/'+source.id+'/content-map')
   .then(data=>{
    if(!alive)return
    setContentSections(data.sections)
    setTemplateSample(data.template_sample)
    if(data.auto_prefill_template && data.template_sample)applyTemplateSample(data.template_sample)
   }).catch(e=>{if(alive)setContentError((e as Error).message)})
  return()=>{alive=false}
 },[source?.id])
 const updateCopy=(key:string,value:string)=>setForm(f=>({...f,content_overrides:{...(f.content_overrides||{}),[key]:value}}))
 const copyEditor=(<>
       {copyFields.length>0&&<div className="accom-copy-panel">
        <div className="accom-copy-panel-heading"><div><strong>Section content</strong><p>Only the fields belonging to this section. Existing values are already loaded.</p></div><span>{copyFields.length} fields</span></div>
        {copyGroups.map(group=><section key={group.name} className="accom-field-frame" aria-label={group.name}>
          <div className="accom-field-frame-title"><strong>{group.name}</strong><span>{group.fields.length} {group.fields.length===1?'field':'fields'}</span></div>
          <div className="accom-field-frame-content">
            {group.fields.map(field=>{
              const value=form.content_overrides?.[field.key]??field.value
              return <label key={field.key} className={'accom-copy-field accom-copy-'+field.kind}>
                <span>{field.label}</span>
                {field.kind==='textarea'?
                  <textarea rows={3} value={value} onChange={e=>updateCopy(field.key,e.target.value)}/>:
                  <input type="text" value={value} onChange={e=>updateCopy(field.key,e.target.value)}
                    placeholder={field.kind==='image'?'https://… or upload a photo':field.kind==='cta_link'?'#rooms, /page or https://…':''}/>}
                {field.kind==='image'&&<>
                  {value&&<img className="accom-copy-photo" src={value} alt="Section image preview" loading="lazy"/>}
                  <input type="file" accept="image/jpeg,image/png,image/webp" aria-label="Upload section image" onChange={async e=>{const file=e.target.files?.[0];if(!file)return;try{updateCopy(field.key,await uploadPhoto(file))}catch(err){setError((err as Error).message)}}}/>
                </>}
                {field.kind==='cta_link'&&<small>Only CTA destinations are editable. Leave navigation links managed by the template.</small>}
                {field.kind==='cta_label'&&<small>Changes the button label; the original click behaviour is retained.</small>}
              </label>
            })}
          </div>
        </section>)}
       </div>}
       {contentError&&<p className="error" role="alert">{contentError}</p>}
       {!copyFields.length&&!contentError&&<p className="accom-fields-help">{source?'Loading section content…':'Save your draft to load its section content.'}</p>}

 </>)
 const previewSignature=JSON.stringify(form)
 useEffect(()=>{
  if(!source?.id){setPreviewHtml('');return}
  let cancelled=false
  const timer=window.setTimeout(async()=>{
   setPreviewLoading(true);setPreviewError('')
   try{
    const response=await fetch('/api/admin/properties/'+source.id+'/preview-draft',{
     method:'POST',
     headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},
     body:previewSignature
    })
    if(!response.ok)throw new Error('Could not render preview ('+response.status+').')
    const html=await response.text()
    if(!cancelled)setPreviewHtml(html)
   }catch(err){if(!cancelled)setPreviewError((err as Error).message)}
   finally{if(!cancelled)setPreviewLoading(false)}
  },480)
  return()=>{cancelled=true;window.clearTimeout(timer)}
 },[source?.id,previewSignature])
 useEffect(()=>{
  const node=previewContainerRef.current
  if(!node)return
  const resize=()=>{
   const width=previewMode==='desktop'?1280:390
   setPreviewScale(Math.max(.15,Math.min(1,(node.clientWidth-20)/width)))
  }
  resize()
  const obs=new ResizeObserver(resize)
  obs.observe(node)
  return()=>obs.disconnect()
 },[previewMode])
 useEffect(()=>{
  if(!previewHtml)return
  const frame=previewFrameRef.current
  if(!frame)return
  try{
   const selector=MASTER_PREVIEW_SELECTOR[activeSection]
   frame.contentDocument?.querySelector(selector)?.scrollIntoView({block:'start',behavior:'instant'})
  }catch{ /* A browser can restrict frame access; the preview still renders. */ }
 },[activeSection,previewHtml])
 const openFullPreview=()=>{
  if(sourceReference){
   window.open('/accom-live/index.html','_blank','noopener')
   return
  }
  if(!previewHtml){setPreviewError('Complete a saved draft to enable the full preview.');return}
  const tab=window.open('about:blank','_blank')
  if(!tab){setPreviewError('Allow pop-ups to open the preview.');return}
  tab.document.open();tab.document.write(previewHtml);tab.document.close()
 }
 const previewWidth=previewMode==='desktop'?1280:390
 
 return <div className="drawer-shade accom-editor-overlay" role="presentation">
  {seoOpen&&<div className="accom-seo-modal-backdrop" role="presentation">
   <section className="accom-seo-modal" role="dialog" aria-modal="true" aria-label="Page SEO settings">
    <div className="accom-seo-modal-header"><div><span className="eyebrow">PAGE SETTINGS</span><h3>SEO & publishing</h3><p>Search metadata is separate from the 13 visible page sections.</p></div><button type="button" aria-label="Close SEO settings" onClick={()=>setSeoOpen(false)}><X size={17}/></button></div>
    <div className="accom-seo-modal-fields">
     <label>Page URL slug<input value={form.slug||''} onChange={e=>set('slug',e.target.value)} placeholder="Auto-created from the property name"/></label>
     <label>SEO title<input maxLength={250} value={form.seo_title||''} onChange={e=>set('seo_title',e.target.value)}/></label>
     <label>Meta description<textarea rows={3} maxLength={400} value={form.meta_description||''} onChange={e=>set('meta_description',e.target.value)}/></label>
     <label className="checkline"><input type="checkbox" checked={!!form.noindex} onChange={e=>set('noindex',e.target.checked)}/> Prevent indexing (noindex)</label>
     <label className="checkline"><input type="checkbox" checked={!!form.is_demo} onChange={e=>set('is_demo',e.target.checked)}/> Demo content — publishing blocked until verified</label>
     <p className="accom-fields-help">This panel changes page metadata and draft status only. Publishing remains an administrator action in All Pages.</p>
    </div>
    <div className="accom-seo-modal-footer"><button type="button" className="primary compact" onClick={()=>setSeoOpen(false)}>Back to editor</button></div>
   </section>
  </div>}
  <div className="accom-editor-shell" role="region" aria-label="Accom Category page editor">
   <aside className="category-sidebar accom-editor-site-sidebar" aria-label="Content manager navigation">
    <div className="category-sidebar-brand"><Logo/><small>CONTENT MANAGER</small></div>
    <nav aria-label="Category"><button className="category-sidebar-item active" type="button" onClick={safeClose}>Category</button></nav>
    <div className="category-sidebar-spacer"/>
    <div className="admin-side-bottom"><strong>Content workspace</strong><small>Page editor</small></div>
    <button type="button" className="category-exit" onClick={safeClose}>All Pages <ArrowRight size={14}/></button>
   </aside>
   <div className="accom-editor-main">
    <div className="accom-editor-topbar"><div>Category <ChevronRight size={13}/> <strong>Page Editor</strong></div><span><span className="accom-editor-local-dot"/> LOCAL WORKSPACE</span></div>
    <div className="accom-editor-content">
    <div className="drawer accom-page-editor">
   <header className="accom-editor-header">
    <div className="accom-editor-title">
     <button type="button" className="accom-editor-back" onClick={safeClose}><ChevronLeft size={15}/> Back to pages</button>
     <div className="accom-editor-title-line"><h1>{form.name||'Untitled accommodation'}</h1><span className="accom-editor-status">{source?.published?'Published':'Draft'}</span></div>
     <p>Accommodation Page <span aria-hidden="true">·</span> /{form.slug||'new-page'}/</p>
    </div>
    <div className="accom-editor-head-actions">
      <span className={'accom-editor-saving-state '+(dirty?'unsaved':'')}>{busy?'Saving…':dirty?'Unsaved changes':'Saved'}</span>
      <button type="button" className="outline" onClick={()=>setSeoOpen(true)}><Search size={15}/> SEO settings</button>
      <button type="button" className="outline" onClick={openFullPreview} disabled={!sourceReference&&!previewHtml}> <ImageIcon size={15}/> Preview</button>
      <button type="submit" form="accom-property-edit-form" className="primary" disabled={busy}><Check size={15}/>{busy?'Saving…':'Save draft'}</button>
    </div>
   </header>
   {error&&<p className="error accom-editor-inline-error" role="alert">{error}</p>}
   <form id="accom-property-edit-form" onSubmit={submit} className="drawer-form accom-editor-form">
    <div className="accom-editor-workspace">
     <aside className="accom-editor-sidebar" aria-label="Page sections">
      <div className="accom-editor-pane-heading"><strong>Edit sections</strong><span>{sections.length} sections</span></div>
      <nav className="accom-editor-sections" aria-label="Choose editing section">
       {sections.map(item=>{const Icon=item.icon;return <button type="button" key={item.id} aria-current={activeSection===item.id?'step':undefined} className={'accom-editor-section-nav '+(activeSection===item.id?'active':'')} onClick={()=>{setActiveSection(item.id);fieldsPanelRef.current?.scrollTo({top:0,behavior:'instant'})}}><Icon size={15}/><span>{item.title}</span><span className="accom-editor-section-index">{item.index}</span></button>})}
      </nav>
      <div className="accom-editor-side-note">Fields follow the approved property layout. <button type="button" onClick={()=>{setSourceReference(true);setSourceSection('top')}}>View original design</button></div>
     </aside>
     <main ref={fieldsPanelRef} className="accom-editor-fields" aria-live="off">
      <div className="accom-editor-fields-head"><span className="eyebrow">SECTION {currentSection.index}</span><h3>{currentSection.title}</h3><p>{currentSection.desc}</p></div>
      <div className="accom-editor-fields-body">
       {activeSection!=='top'&&copyEditor}

       {activeSection==='top'&&<div className="accom-fields-group">
        <label>Property name<input required minLength={3} value={form.name} onChange={e=>set('name',e.target.value)}/></label>
        <div className="form-grid"><label>City<input required value={form.city} onChange={e=>set('city',e.target.value)}/></label><label>Country<input value={form.country} onChange={e=>set('country',e.target.value)}/></label><label>Postcode<input value={form.postcode} onChange={e=>set('postcode',e.target.value)}/></label><label>Nearby university<input value={form.university} onChange={e=>set('university',e.target.value)}/></label></div>
        <label>Address<input value={form.address} onChange={e=>set('address',e.target.value)}/></label>
        <RepeatableField title="Hero gallery photos" items={form.gallery} create={()=>({url:'',alt:'',category:'Rooms',layout:'regular' as const})} onChange={v=>set('gallery',v)} describe={(v,i)=>v.alt||v.category||('Picture '+(i+1))} help="Use approved photos. Choose Regular or Large for the original gallery layout." render={(item,change)=>media(item,change,'Property')}/>
       </div>}
       {activeSection==='overview'&&<div className="accom-fields-group">
        <label>Overview / property description<textarea rows={4} value={form.description} onChange={e=>set('description',e.target.value)}/></label>
        <RepeatableField title="Property highlights" items={form.highlights.map((title,i)=>({title,detail:form.highlight_descriptions[i]||''}))} create={()=>({title:'',detail:''})} onChange={v=>setForm(f=>({...f,highlights:v.map(item=>item.title),highlight_descriptions:v.map(item=>item.detail)}))} describe={v=>v.title||'New highlight'} render={(v,change)=><><label>Highlight title<input value={v.title} onChange={e=>change({...v,title:e.target.value})}/></label><label>Highlight description<textarea rows={2} value={v.detail} onChange={e=>change({...v,detail:e.target.value})}/></label></>}/>
       </div>}
       {activeSection==='tours'&&<div className="accom-fields-group">
        <label>Virtual tour link<input type="url" value={form.tour_url||''} onChange={e=>set('tour_url',e.target.value)}/></label>
        <p className="accom-fields-help">Gallery photos are managed in Hero & gallery. This section includes the original photo-category and tour copy below.</p>
       </div>}
       {activeSection==='amenities'&&<div className="accom-fields-group">
        <RepeatableField title="Amenities" items={form.amenities} create={()=>''} onChange={v=>set('amenities',v)} describe={v=>v||'New amenity'} render={(v,change)=><label>Amenity<input value={v} onChange={e=>change(e.target.value)}/></label>}/>
       </div>}
       {activeSection==='rooms'&&<div className="accom-fields-group">
        <div className="accom-room-editor-heading"><strong>Room inventory & tenancy plans</strong><span>{source?.rooms?.length||0} room records</span></div>
        {source?.rooms?.length?source.rooms.map(room=><div className="accom-room-editor-row" key={room.id}>
          <div><strong>{room.name}</strong><small>{room.room_type} · {room.availability} · {room.price===null?'Price on request':money(room.price,room.currency,room.price_period)}</small><small>{room.tenancies?.length||0} tenancy options</small></div>
          <button type="button" className="outline tiny" onClick={()=>{if(dirty&&!window.confirm('Discard unsaved page changes to edit this room?'))return;editRoom(room)}}>Edit room</button>
        </div>):<p className="accom-fields-help">No room types have been entered for this property yet.</p>}
        <button type="button" className="outline compact" disabled={!source} onClick={()=>{if(dirty&&!window.confirm('Discard unsaved page changes to manage rooms?'))return;editRoom(null)}}>Add / manage rooms and tenancy options</button>
       </div>}
       {activeSection==='rules'&&<div className="accom-fields-group">
        <RepeatableField title="House rules and policies" items={form.policies} create={()=>({question:'',answer:''})} onChange={v=>set('policies',v)} describe={v=>v.question||'New policy'} render={(v,change)=><><label>Policy title<input value={v.question} onChange={e=>change({...v,question:e.target.value})}/></label><label>Details<textarea rows={2} value={v.answer} onChange={e=>change({...v,answer:e.target.value})}/></label></>}/>
       </div>}
       {activeSection==='payments'&&<div className="accom-fields-group">
        <RepeatableField title="Offers and promotions" items={form.offers} create={()=>({title:'',description:'',valid_until:''})} onChange={v=>set('offers',v)} describe={v=>v.title||'New offer'} render={(v,change)=><><label>Offer title<input value={v.title} onChange={e=>change({...v,title:e.target.value})}/></label><label>Details<textarea rows={2} value={v.description} onChange={e=>change({...v,description:e.target.value})}/></label><label>Valid until<input type="date" value={v.valid_until||''} onChange={e=>change({...v,valid_until:e.target.value})}/></label></>}/>
       </div>}
       {activeSection==='floorplan'&&<div className="accom-fields-group">
        <RepeatableField title="Floor-plan images" items={form.floorplans} create={()=>({url:'',alt:'',category:'Floor plan',layout:'regular' as const})} onChange={v=>set('floorplans',v)} describe={(v,i)=>v.alt||('Floor plan '+(i+1))} render={(v,change)=>media(v,change,'Floor plan')}/>
       </div>}
       {activeSection==='faqs'&&<div className="accom-fields-group">
        <RepeatableField title="Frequently asked questions" items={form.faq} create={()=>({question:'',answer:''})} onChange={v=>set('faq',v)} describe={v=>v.question||'New FAQ'} render={(v,change)=><><label>Question<input value={v.question} onChange={e=>change({...v,question:e.target.value})}/></label><label>Answer<textarea rows={2} value={v.answer} onChange={e=>change({...v,answer:e.target.value})}/></label></>}/>
       </div>}
       {activeSection==='location'&&<div className="accom-fields-group">
        <RepeatableField title="Nearby landmarks" items={form.landmarks} create={()=>({name:'',detail:''})} onChange={v=>set('landmarks',v)} describe={v=>v.name||'New landmark'} render={(v,change)=><><label>Landmark<input value={v.name} onChange={e=>change({...v,name:e.target.value})}/></label><label>Distance / description<input value={v.detail} onChange={e=>change({...v,detail:e.target.value})}/></label></>}/>
       </div>}
       {activeSection==='reviews'&&<div className="accom-fields-group">
        <RepeatableField title="Student reviews" items={form.reviews} create={()=>({name:'',quote:'',source_url:''})} onChange={v=>set('reviews',v)} describe={v=>v.name||'New review'} help="Only enter reviews authorised for publication." render={(v,change)=><><label>Reviewer<input value={v.name} onChange={e=>change({...v,name:e.target.value})}/></label><label>Review<textarea rows={2} value={v.quote} onChange={e=>change({...v,quote:e.target.value})}/></label><label>Source URL<input type="url" value={v.source_url} onChange={e=>change({...v,source_url:e.target.value})}/></label></>}/>
        <label>Review source URL<input type="url" value={form.review_source_url||''} onChange={e=>set('review_source_url',e.target.value)}/></label>
        <div className="form-grid"><label>Review score (0–5)<input type="number" min="0" max="5" step=".1" value={form.review_score??''} onChange={e=>set('review_score',e.target.value?Number(e.target.value):null)}/></label><label>Review count<input type="number" min="0" value={form.review_count??''} onChange={e=>set('review_count',e.target.value?Number(e.target.value):null)}/></label></div>
       </div>}
       {activeSection==='top'&&copyEditor}

      </div>
     </main>
     <section className="accom-editor-preview" aria-label="Complete Accom property preview">
      <div className="accom-editor-preview-head">
        <div className="accom-editor-preview-label"><h3>Live Preview</h3><small>{sourceReference?'Approved original page · read-only':'Actual property layout · updates as you type'}</small></div>
        <div className="accom-editor-preview-controls">
         <div className="accom-preview-mode-switch" role="group" aria-label="Preview source">
          <button type="button" className={!sourceReference?'active':''} aria-pressed={!sourceReference} onClick={()=>setSourceReference(false)}>Draft</button>
          <button type="button" className={sourceReference?'active':''} aria-pressed={sourceReference} onClick={()=>setSourceReference(true)}>Original</button>
         </div>
         <div className="accom-editor-device-toggle" aria-label="Preview viewport"><button type="button" aria-pressed={previewMode==='desktop'} className={previewMode==='desktop'?'active':''} onClick={()=>setPreviewMode('desktop')}>Desktop</button><button type="button" aria-pressed={previewMode==='mobile'} className={previewMode==='mobile'?'active':''} onClick={()=>setPreviewMode('mobile')}>Mobile</button></div>
         <button type="button" className="accom-editor-expand-preview" onClick={openFullPreview} disabled={!sourceReference&&!previewHtml} aria-label="Expand full preview" title="Open full page"><ArrowRight size={15}/></button>
        </div>
       </div>
       {sourceReference&&<div className="accom-original-section-picker"><label>Jump to section <select value={sourceSection} aria-label="Jump to page section" onChange={e=>jumpSource(e.target.value)}>{sourceSections.map(section=><option key={section.id} value={section.id}>{section.name}</option>)}</select></label></div>}
      <div className="accom-editor-preview-viewport" ref={previewContainerRef}>
       {(sourceReference||previewHtml)?<div className={'accom-editor-preview-paper '+(previewMode==='mobile'?'mobile':'desktop')} style={{width:previewWidth*previewScale,height:1550*previewScale}}>
         <iframe key={sourceReference?'source':'draft'} ref={previewFrameRef} title={sourceReference?'Complete original Accom source page':'Live property page visual preview'} sandbox={sourceReference?'allow-scripts allow-popups':'allow-scripts allow-same-origin'} src={sourceReference?'/accom-live/index.html':undefined} srcDoc={sourceReference?undefined:previewHtml} className={sourceReference?'accom-source-frame':''} style={{width:previewWidth,height:1550,transform:'scale('+previewScale+')',transformOrigin:'top left'}} onLoad={e=>{if(sourceReference){e.currentTarget.contentWindow?.postMessage({type:'accom-open-section',id:sourceSection},'*');return}try{const target=MASTER_PREVIEW_SELECTOR[activeSection];e.currentTarget.contentDocument?.querySelector(target)?.scrollIntoView({block:'start',behavior:'instant'})}catch{}}}/>
        </div>:<div className="accom-editor-preview-empty"><ImageIcon size={30}/><strong>{source?'Preparing draft preview':'Save a draft to preview its data'}</strong></div>}
      </div>
      <div className="accom-editor-preview-foot"><span>{sourceReference?'Original template · select Draft to see edits.':previewLoading?'Updating preview…':previewError||'Preview only · Changes are not published'}</span></div>
     </section>
    </div>
   </form>
  </div>
  </div>
  </div>
  </div>
 </div>
}

function RoomManager({p,close,saved,current,setCurrent}:{p:Property;close:()=>void;saved:()=>void;current:Room|null;setCurrent:(r:Room|null)=>void}){const [form,setForm]=useState({...blankRoom,...(current||{})}),[error,setError]=useState(''),[busy,setBusy]=useState(false);const set=(k:string,v:unknown)=>setForm(f=>({...f,[k]:v}));const submit=async(e:React.FormEvent)=>{e.preventDefault();setBusy(true);setError('');try{await api(current?'/api/admin/rooms/'+current.id:'/api/admin/properties/'+p.id+'/rooms',{method:current?'PATCH':'POST',body:JSON.stringify({...form,edit_version:current?.edit_version??null,parent_edit_version:p.edit_version})});saved()}catch(e){setError((e as Error).message)}finally{setBusy(false)}};return <div className="drawer-shade"><div className="drawer" role="dialog" aria-modal="true" aria-label="Room editor"><div className="drawer-header"><div><span className="eyebrow">ROOM INVENTORY · {p.name}</span><h2>{current?'Edit room':'Manage room types'}</h2></div><button onClick={close}><X/></button></div><div className="room-pickers">{p.rooms?.map(r=><button key={r.id} onClick={()=>{setCurrent(r);setForm({...blankRoom,...r})}}>{r.name} · {money(r.price,r.currency,r.price_period)} <ArrowRight size={12}/></button>)}</div><form className="drawer-form" onSubmit={submit}><h3>{current?'Edit this room':'Add a new room'}</h3><label>Room name<input required minLength={2} value={form.name} onChange={e=>set('name',e.target.value)}/></label><div className="form-grid"><label>Room category<select value={form.room_type} onChange={e=>set('room_type',e.target.value)}><option>En suite</option><option>Studio</option><option>Shared</option><option>Apartment</option></select></label><label>Availability<select value={form.availability} onChange={e=>set('availability',e.target.value)}><option value="enquire">Confirm on enquiry</option><option value="available">Available</option><option value="unavailable">Unavailable</option></select></label><label>Price<input type="number" min="0" step=".01" value={form.price??''} onChange={e=>set('price',e.target.value?Number(e.target.value):null)}/></label><label>Currency<input value={form.currency} maxLength={3} onChange={e=>set('currency',e.target.value.toUpperCase())}/></label><label>Rate period<select value={form.price_period} onChange={e=>set('price_period',e.target.value)}><option value="week">Per week</option><option value="month">Per month</option></select></label><label>Rate checked on<input type="date" value={form.rate_checked_at||''} onChange={e=>set('rate_checked_at',e.target.value||null)}/></label><label>Available from<input type="date" value={form.available_from||''} onChange={e=>set('available_from',e.target.value||null)}/></label><label>Size in m²<input type="number" min="0" step=".01" value={form.size_sqm??''} onChange={e=>set('size_sqm',e.target.value?Number(e.target.value):null)}/></label><label>Bathroom<input value={form.bathroom} onChange={e=>set('bathroom',e.target.value)}/></label><label>Kitchen<input value={form.kitchen} onChange={e=>set('kitchen',e.target.value)}/></label></div><label>Description<textarea rows={3} value={form.details} onChange={e=>set('details',e.target.value)}/></label><label>Room image URL<input value={form.image_url} onChange={e=>set('image_url',e.target.value)}/></label><label>Or upload a room photo<input type="file" accept="image/jpeg,image/png,image/webp" onChange={async e=>{const f=e.target.files?.[0];if(!f)return;try{set('image_url',await uploadPhoto(f))}catch(err){setError((err as Error).message)}}}/></label><label>Image description (alt text)<input value={form.image_alt||''} onChange={e=>set('image_alt',e.target.value)}/></label><fieldset className="image-layout-switch"><legend>Room image appearance</legend><div className="layout-switch">{(['regular','large'] as const).map(v=><button type="button" className={form.image_layout===v?'selected':''} onClick={()=>set('image_layout',v)} key={v}>{v==='regular'?'Regular':'Large'}</button>)}</div></fieldset><TenancyEditor value={form.tenancies||[]} onChange={value=>set('tenancies',value)}/><label>Rate source URL<input value={form.source_url} onChange={e=>set('source_url',e.target.value)}/></label><label className="checkline"><input type="checkbox" checked={form.active} onChange={e=>set('active',e.target.checked)}/> Active room listing</label>{error&&<p className="error">{error}</p>}<div className="drawer-footer editor-sticky-footer"><button type="button" className="outline" onClick={close}>Close</button><button className="primary" disabled={busy}>{busy?'Saving…':'Save room'}</button></div></form></div></div>}
function Support({go}:{go:(s:string)=>void}){return <main className="wrap support-page"><span className="eyebrow">STUDENT SUPPORT</span><h1>Need help finding your accommodation?</h1><p>Open a property to send your enquiry directly to the Accom team. If you have an account, you can track its progress in your student portal.</p><div className="quick-actions"><button className="primary" onClick={()=>go('/')}>Explore accommodation</button><button className="outline" onClick={()=>go('/student')}>My student portal</button></div></main>}
function VerifyEmailPage({go}:{go:(s:string)=>void}){const [text,setText]=useState('Checking verification…');useEffect(()=>{const code=new URLSearchParams(window.location.search).get('token');if(!code){setText('Verification token missing.');return}api('/api/auth/verify-email',{method:'POST',body:JSON.stringify({token:code})}).then(()=>setText('Your email is verified. You can now sign in.')).catch(e=>setText(e.message))},[]);return <main className="wrap support-page"><h1>Email verification</h1><p>{text}</p><button className="primary" onClick={()=>go('/login')}>Go to sign in</button></main>}
export default function App(){const [path,setPath]=useState(readPath),[user,setUser]=useState<User|null>(null),[ready,setReady]=useState(false);const go=(next:string)=>{if(next.startsWith('/property/')){window.location.assign(next);return}history.pushState({},'',next);setPath(next);window.scrollTo({top:0,behavior:'instant'})};const logout=()=>{token='';sessionStorage.removeItem('accom_token');setUser(null);go('/login')};useEffect(()=>{const pop=()=>setPath(readPath());window.addEventListener('popstate',pop);if(token)api<User>('/api/me').then(setUser).catch(()=>{token='';sessionStorage.removeItem('accom_token')}).finally(()=>setReady(true));else setReady(true);return()=>window.removeEventListener('popstate',pop)},[]);useEffect(()=>{
  if(!ready)return
  if(path==='/admin'&&(!user||user.role==='student')){
    history.replaceState({},'', '/login')
    setPath('/login')
  }
},[ready,path,user?.role])
if(!ready)return <div className="loading">Opening Accom…</div>;
const routedPath=path==='/admin'&&(!user||user.role==='student')?'/login':path;
const inAdmin=routedPath==='/admin';return <>{!inAdmin&&<Header go={go} user={user} logout={logout} hideExplore={routedPath==='/login'||routedPath==='/register'}/>}<>{routedPath.startsWith('/property/')?<Listing slug={decodeURIComponent(routedPath.split('/')[2]||'')} go={go} user={user}/>:(routedPath==='/login'||routedPath==='/register')?<Auth key={path} go={go} setUser={setUser} registration={routedPath==='/register'}/>:routedPath==='/student'?<Student go={go} user={user}/>:inAdmin?<Admin go={go} user={user}/>:routedPath==='/help'?<Support go={go}/>:routedPath==='/verify-email'?<VerifyEmailPage go={go}/>:<Directory go={go} user={user}/>}</>{!inAdmin&&<footer className="site-footer"><div className="wrap"><Logo/><span>Student accommodation, made simpler.</span><span>© {new Date().getFullYear()} Accom by Emlen</span></div></footer>}</>}
