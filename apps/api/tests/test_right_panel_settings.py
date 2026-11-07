"""Advanced robots directives and section static controls are persisted safely."""
from bs4 import BeautifulSoup
from test_flow import client, sign_in, draft, published

def meta(html):
    soup=BeautifulSoup(html,"html.parser")
    return soup.select_one('meta[name="robots"]')["content"]

def test_advanced_robots_options_survive_save_and_render(client):
    auth=sign_in(client)
    record,_=published(client,auth)
    url=f"/api/admin/properties/{record['id']}"
    next_data={**record,"noarchive":True,"noimageindex":True,"nosnippet":True,
               "nofollow":True,"noindex":False,"static_sections":["gallery","payments"]}
    saved=client.patch(url,headers=auth,json=next_data)
    assert saved.status_code==200,saved.text
    result=saved.json()
    assert result["static_sections"]==["gallery","payments"]
    assert result["noarchive"] and result["noimageindex"] and result["nosnippet"]
    assert meta(client.get("/property/"+record["slug"]).text)=="index,nofollow,noarchive,noimageindex,nosnippet"
    draft_html=client.post(url+"/preview-draft",headers=auth,
                          json={"noindex":False,"nofollow":False,"noarchive":True,
                                "noimageindex":True,"nosnippet":True})
    assert draft_html.status_code==200
    assert meta(draft_html.text)=="noindex,nofollow,noarchive,noimageindex,nosnippet"

def test_reject_unrecognized_or_duplicate_static_sections(client):
    auth=sign_in(client)
    p=draft(client,auth,name="Static Lock Test Residence")
    url=f"/api/admin/properties/{p['id']}"
    for value in [["missing-section"],["top","top"],["seo"]]:
        response=client.patch(url,headers=auth,json={**p,"static_sections":value})
        assert response.status_code==422,value
