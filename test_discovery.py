import pytest
from discovery import discovery_queries, safe_source_url, init_discovery, save_lead, get_leads, edit_lead
from core import connect

def test_discovery_queries():
    queries=discovery_queries(['Product Manager'],['Visa'],['Northwestern University'],3)
    assert len(queries)==2
    assert all('-site:linkedin.com' in q for q in queries)

def test_safe_sources():
    assert safe_source_url('https://example.org/people/jane')
    assert not safe_source_url('https://www.linkedin.com/in/jane')
    assert not safe_source_url('http://example.org')
    assert not safe_source_url('javascript:alert(1)')

def test_leads_review(tmp_path):
    con=connect(tmp_path/'test.db')
    init_discovery(con)
    item=dict(url='https://example.org/bio',title='Jane Bio',snippet='Product manager')
    save_lead(con,item)
    save_lead(con,item)
    rows=get_leads(con)
    assert len(rows)==1
    edit_lead(con,rows[0]['id'],'Jane','Visa','PM','Verified')
    assert get_leads(con)[0]['name']=='Jane'
    assert get_leads(con)[0]['review_status']=='Verified'
    with pytest.raises(ValueError): save_lead(con,dict(url='https://www.linkedin.com/in/jane'))
