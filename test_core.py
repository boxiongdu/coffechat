import sqlite3
from datetime import date
from core import connect, add_contact, score, set_status, get_contact, normalize_linkedin, manual_draft, seed_demo

def test_score():
    assert score({'fintech':1,'pm_role':1,'shared_school':1,'relevant_transition':1,'alumni':1})[0] == 100
    assert score({})[0] == 0

def test_url():
    assert normalize_linkedin('www.linkedin.com/in/Example/?trk=abc') == 'https://www.linkedin.com/in/example/'
    try:
        normalize_linkedin('https://malicious.example/in/test')
        assert False
    except ValueError: pass

def test_database_and_followup(tmp_path):
    con=connect(tmp_path/'test.db')
    cid=add_contact(con, {'name':'Test Person','linkedin_url':'https://www.linkedin.com/in/test/'})
    set_status(con,cid,'Invitation sent',date(2026,10,29))
    c=get_contact(con,cid)
    assert c['next_followup']=='2026-11-07'
    assert 'Hi Test' in manual_draft(c,'connection')
    set_status(con,cid,'Replied',date(2026,10,30))
    assert get_contact(con,cid)['next_followup']==''

def test_seed(tmp_path):
    con=connect(tmp_path/'demo.db')
    assert seed_demo(con) is True
    assert seed_demo(con) is False
    assert score(dict(con.execute('SELECT * FROM contacts').fetchone()))[0]==70
