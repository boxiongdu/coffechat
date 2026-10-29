"""Candidate discovery through an authorized search API; no LinkedIn site automation."""
import sqlite3
from urllib.parse import urlparse
import requests

TARGET_ROLES = ['Associate Product Manager', 'Product Manager', 'Technical Product Manager', 'AI Product Manager']
TARGET_COMPANIES = ['Visa', 'Stripe', 'Block', 'Mastercard', 'Capital One', 'PayPal']
TARGET_SCHOOLS = ['Northwestern University', 'Vassar College']


def discovery_queries(roles=None, companies=None, schools=None, limit=12):
    roles = roles or TARGET_ROLES
    companies = companies or TARGET_COMPANIES
    schools = schools or TARGET_SCHOOLS
    # Discover via independently published employee biographies, interviews, and websites.
    # Do not target LinkedIn profiles through another search provider.
    queries = []
    for company in companies:
        for role in roles[:2]:
            queries.append(f'"{company}" "{role}" biography -site:linkedin.com -site:linkedin.cn')
        for school in schools[:1]:
            queries.append(f'"{company}" "{school}" product management biography -site:linkedin.com')
    return queries[:limit]


def safe_source_url(url):
    try:
        p = urlparse(url)
        host = (p.hostname or '').lower()
        return p.scheme == 'https' and bool(host) and host not in ('linkedin.com','www.linkedin.com','linkedin.cn','www.linkedin.cn')
    except ValueError:
        return False


def brave_search(query, api_key, count=8):
    if not api_key:
        raise ValueError('Add a Brave Search API key in the sidebar to run public-web discovery.')
    response = requests.get('https://api.search.brave.com/res/v1/web/search',
        params={'q': query, 'count': min(max(count, 1), 20), 'safesearch': 'moderate'},
        headers={'X-Subscription-Token': api_key, 'Accept':'application/json'}, timeout=18)
    response.raise_for_status()
    items = response.json().get('web', {}).get('results', [])
    return [dict(title=i.get('title',''),url=i.get('url',''),snippet=i.get('description',''),query=query)
            for i in items if safe_source_url(i.get('url',''))]


def init_discovery(con):
    con.execute('''CREATE TABLE IF NOT EXISTS discovery_leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT DEFAULT '',
        company TEXT DEFAULT '', role TEXT DEFAULT '', source_url TEXT NOT NULL UNIQUE,
        source_title TEXT DEFAULT '', evidence TEXT DEFAULT '',
        review_status TEXT NOT NULL DEFAULT 'Needs review',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    con.commit()


def save_lead(con, item):
    url=item.get('url','').strip()
    if not safe_source_url(url):
        raise ValueError('Lead requires an HTTPS public-web source outside LinkedIn.')
    with con:
        con.execute('''INSERT INTO discovery_leads(source_url,source_title,evidence)
            VALUES(?,?,?) ON CONFLICT(source_url) DO UPDATE SET
            source_title=excluded.source_title,evidence=excluded.evidence''',
            (url,item.get('title','')[:500],item.get('snippet','')[:3000]))


def get_leads(con):
    init_discovery(con)
    return [dict(row) for row in con.execute('SELECT * FROM discovery_leads ORDER BY id DESC')]


def edit_lead(con, lead_id, name, company, role, status):
    if status not in ('Needs review','Verified','Dismissed','Added to CRM'):
        raise ValueError('Invalid lead status')
    with con:
        con.execute('UPDATE discovery_leads SET name=?,company=?,role=?,review_status=? WHERE id=?',
                    (name[:200],company[:200],role[:200],status,lead_id))


def extract_profile_notes(text):
    """Treat manually supplied profile text as evidence, not verified structured facts."""
    text=text.strip()
    if len(text)>6000:
        raise ValueError('Please paste at most 6,000 characters.')
    return text
