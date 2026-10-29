import os
from datetime import date
import pandas as pd
import streamlit as st
from discovery import (discovery_queries, search_url, init_discovery, save_lead, get_leads, edit_lead, extract_profile_notes)
from core import (STAGES, connect, get_contacts, get_contact, score, add_contact,
                  set_status, save_draft, manual_draft, csv_export, seed_demo)

st.set_page_config(page_title='Networking Agent', page_icon='🤝', layout='wide')
st.title('🤝 Networking Agent')
st.caption('A human-in-the-loop CRM for targeted coffee chats. Never scrapes LinkedIn or sends messages automatically.')
con = connect(os.getenv('NETWORKING_DB', 'networking.db'))
init_discovery(con)

with st.sidebar:
    st.header('Settings')
    st.caption('No API keys needed. Candidate discovery and message drafts are human-reviewed.')
    st.divider()
    if st.button('Add example: Darrian Mankin', use_container_width=True):
        if seed_demo(con): st.success('Example added')
        else: st.info('Contacts already exist; sample not added')
    st.info('Review every draft. Open LinkedIn yourself to send invitations or messages. Record a stage change after sending.')

contacts = get_contacts(con)
for c in contacts:
    c['score'], _ = score(c)

now = date.today().isoformat()
due = [c for c in contacts if c['next_followup'] and c['next_followup'] <= now and c['status'] in ('Invitation sent', 'Coffee chat requested')]
cols = st.columns(4)
for col, label, value in zip(cols, ['Contacts', 'Pending invitations', 'Chats scheduled', 'Follow-ups due'],
                             [len(contacts), sum(c['status']=='Invitation sent' for c in contacts),sum(c['status']=='Scheduled' for c in contacts),len(due)]):
    col.metric(label, value)

tab0,tab1,tab2,tab3,tab4 = st.tabs(['🔎 Discover candidates', '📋 Pipeline', '➕ Add contact', '✍️ Outreach workspace', '⏰ Follow-ups'])
with tab0:
    st.subheader('Discover candidates')
    st.caption('Open public-web searches yourself, save relevant pages to a review inbox, and verify details before promotion. No API key, scraping, or automatic outreach.')
    st.caption('Enter multiple values separated by commas or new lines.')
    companies_text = st.text_area('Target companies', value='Visa, Stripe, Block', height=75, placeholder='Visa, Stripe, Capital One')
    roles_text = st.text_area('Current roles', value='Associate Product Manager, Product Manager', height=75, placeholder='Associate Product Manager, Data Scientist')
    schools_text = st.text_input('Shared background (optional)', value='', placeholder='Northwestern University, Vassar College — or leave blank')
    def parse_targets(value):
        return list(dict.fromkeys(part.strip() for part in value.replace('\\n', ',').split(',') if part.strip()))
    companies = parse_targets(companies_text)
    roles = parse_targets(roles_text)
    schools = parse_targets(schools_text)
    max_queries=st.slider('Maximum search queries',1,24,8)
    queries=discovery_queries(roles,companies,schools,max_queries) if companies and roles else []
    if not companies or not roles:
        st.info('Enter at least one target company and one current role to generate searches.')
    with st.expander('Preview searches'):
        for q in queries: st.code(q)
    st.markdown('#### Open a public-web search')
    for idx, q in enumerate(queries):
        st.link_button(f"Search {idx+1}: {q[:85]}", search_url(q))
    st.caption('Search opens in your browser; the app does not automatically collect results.')
    with st.form('add_public_source'):
        source_url = st.text_input('Public page URL (HTTPS; not LinkedIn)')
        source_title = st.text_input('Page title')
        source_excerpt = st.text_area('Relevant profile evidence / short notes')
        if st.form_submit_button('Save public page to research inbox'):
            try:
                save_lead(con, {'url': source_url, 'title': source_title, 'snippet': source_excerpt})
                st.success('Source saved for verification. Review it below.')
            except Exception as e:
                st.error(f'Could not save source: {e}')
    st.divider()
    st.markdown('#### Research inbox')
    leads=get_leads(con)
    if not leads: st.info('No saved public-web pages yet. Open a suggested search and add promising pages, or use LinkedIn-assisted review below.')
    for item in leads:
        if item['review_status']=='Dismissed': continue
        with st.expander(f"{item['source_title'] or item['source_url']} · {item['review_status']}"):
            st.write(item['evidence'] or 'No snippet provided')
            st.link_button('Open source for verification', item['source_url'])
            with st.form(f"review_{item['id']}"):
                a,b,c=st.columns(3)
                with a: n=st.text_input('Verified name',item['name'])
                with b: co=st.text_input('Verified company',item['company'])
                with c: ro=st.text_input('Verified role',item['role'])
                stage=st.selectbox('Research status',['Needs review','Verified','Dismissed'],index=['Needs review','Verified','Dismissed'].index(item['review_status']) if item['review_status'] in ('Needs review','Verified','Dismissed') else 1)
                if st.form_submit_button('Save review'):
                    edit_lead(con,item['id'],n,co,ro,stage)
                    st.success('Research review saved. Add verified people to CRM using the Add contact tab.')
            if item['review_status'] == 'Verified' and item['name']:
                with st.form(f"promote_{item['id']}"):
                    st.markdown('**Promote verified lead to CRM**')
                    profile=st.text_input('LinkedIn URL (provided by you, never fetched automatically)')
                    same=st.checkbox('Verified same university', key=f"same_{item['id']}")
                    financial=st.checkbox('Verified fintech domain',key=f"fin_{item['id']}")
                    product=st.checkbox('Verified current PM role',key=f"pm_{item['id']}")
                    transition=st.checkbox('Verified relevant career transition',key=f"trans_{item['id']}")
                    alumni=st.checkbox('Verified alumni/community connection',key=f"alum_{item['id']}")
                    if st.form_submit_button('Add to CRM'):
                        try:
                            cid=add_contact(con,dict(name=item['name'],company=item['company'],title=item['role'],linkedin_url=profile,
                                shared_school=int(same),fintech=int(financial),pm_role=int(product),
                                relevant_transition=int(transition),alumni=int(alumni),
                                notes=f"Verified independent source: {item['source_url']}\nSource summary: {item['evidence']}"))
                            edit_lead(con,item['id'],item['name'],item['company'],item['role'],'Added to CRM')
                            st.success(f'Added contact #{cid} to CRM')
                        except Exception as e: st.error(f'Could not promote: {e}')
    st.divider()
    st.markdown('#### LinkedIn-assisted review (manual browsing)')
    st.write('Open LinkedIn yourself, select a profile you want to consider, then paste a short summary of information you are permitted to use. The app will not read your browser session or control the site.')
    with st.form('pasted_profile'):
        profile_url=st.text_input('LinkedIn URL')
        pasted_name=st.text_input('Person’s name')
        pasted_company=st.text_input('Company')
        pasted_title=st.text_input('Role')
        pasted_notes=st.text_area('Relevant facts you verified (optional)',height=110)
        if st.form_submit_button('Add reviewed profile to CRM'):
            try:
                cid=add_contact(con,dict(name=pasted_name,linkedin_url=profile_url,company=pasted_company,title=pasted_title,notes=extract_profile_notes(pasted_notes)))
                st.success(f'Contact #{cid} saved. Set score criteria in Add contact for more accurate ranking.')
            except Exception as e: st.error(f'Could not add profile: {e}')
with tab1:
    st.subheader('Prioritized contacts')
    if contacts:
        view = pd.DataFrame(contacts).sort_values(['score','id'],ascending=[False,False])
        columns = ['name','company','title','score','status','next_followup','linkedin_url']
        st.dataframe(view[columns], hide_index=True, use_container_width=True,
                     column_config={'linkedin_url':st.column_config.LinkColumn('LinkedIn profile'), 'score':st.column_config.ProgressColumn('Fit score',min_value=0,max_value=100,format='%d')})
        st.download_button('Export CRM CSV', csv_export(get_contacts(con)), 'contacts.csv', 'text/csv')
    else: st.info('No contacts yet. Add someone or load the sample from the sidebar.')
    with st.expander('How scoring works (100 points)'):
        st.write('Fintech domain 25; current PM role 25; shared university 20; relevant transition 20; verified alumni/community connection 10. Factors are manually verified, not inferred from names or demographics.')
with tab2:
    st.subheader('Add a researched contact')
    st.caption('Enter information you verified yourself from a profile, conversation, or public source. A LinkedIn URL alone is not scraped.')
    with st.form('add'):
        left,right=st.columns(2)
        with left:
            name=st.text_input('Name *')
            link=st.text_input('LinkedIn profile URL *')
            company=st.text_input('Company')
            title=st.text_input('Job title')
        with right:
            school=st.text_input('School / organization')
            fintech=st.checkbox('Fintech domain')
            pm_role=st.checkbox('Current PM role')
            shared_school=st.checkbox('Verified same university')
            relevant_transition=st.checkbox('Career transition relevant to my goals')
            alumni=st.checkbox('Verified alumni/community connection (additional)')
        notes=st.text_area('Verified career details / personalization notes')
        submitted=st.form_submit_button('Save contact',type='primary')
        if submitted:
            try:
                add_contact(con,dict(name=name,linkedin_url=link,company=company,title=title,school=school,
                                     fintech=int(fintech),pm_role=int(pm_role),shared_school=int(shared_school),
                                     relevant_transition=int(relevant_transition),alumni=int(alumni),notes=notes))
                st.success('Contact saved. Open Outreach workspace to prepare a message.')
            except Exception as e:
                st.error(f'Could not save: {e}')
with tab3:
    if not contacts: st.info('Add a contact first.')
    else:
        choice=st.selectbox('Choose contact', contacts, format_func=lambda c:f"{c['name']} — {c['company']} ({c['score']}/100)")
        c=get_contact(con,choice['id'])
        value,breakdown=score(c)
        left,right=st.columns([2,1])
        with left:
            st.subheader(f"{c['name']} · {value}/100")
            st.write(f"**{c['title']}** · {c['company']}")
            st.link_button('Open LinkedIn profile (manual)',c['linkedin_url'])
            st.caption(c['notes'] or 'No profile notes entered')
        with right:
            st.write('**Fit score breakdown**')
            for name,pts,maxp in breakdown: st.write(f'{name}: {pts}/{maxp}')
        kind=st.radio('Message type', ['connection','coffee_chat'],format_func=lambda s:'Connection invitation' if s=='connection' else 'Coffee chat request',horizontal=True)
        draft_key='connection_draft' if kind=='connection' else 'chat_draft'
        unique=f"draft_{c['id']}_{kind}"
        if unique not in st.session_state: st.session_state[unique]=c[draft_key] or manual_draft(c,kind)
        if st.button('Generate offline draft'):
            st.session_state[unique]=manual_draft(c,kind)
        st.caption('Templates use your verified contact details; no AI service is called.')
        text=st.text_area('Edit draft before sending',key=unique,height=145)
        if kind=='connection':
            st.caption(f'{len(text)} characters; aim for ≤ 260 for broad compatibility with LinkedIn invitation limits.')
        if st.button('Save reviewed draft',type='primary'):
            save_draft(con,c['id'],kind,text)
            st.success('Draft saved. Copy and send it yourself on LinkedIn.')
        st.code(text,language=None)
        st.divider()
        st.subheader('Track progress')
        stage=st.selectbox('New pipeline stage',STAGES,index=STAGES.index(c['status']))
        if st.button('Save stage and follow-up date'):
            set_status(con,c['id'],stage)
            st.success('Stage updated. Follow-up computed where appropriate.')
        if c['next_followup']: st.write('Current suggested follow-up:', c['next_followup'])
with tab4:
    st.subheader('Suggested follow-up queue')
    st.caption('Dates are reminders, not automated sends. Replying or scheduling clears the follow-up.')
    upcoming=sorted([c for c in contacts if c['next_followup'] and c['status'] in ('Invitation sent','Coffee chat requested')],key=lambda c:c['next_followup'])
    if not upcoming: st.success('No pending follow-ups. Record outreach stages in the workspace.')
    for c in upcoming:
        status='🔴 Due' if c['next_followup']<=now else '🗓️ Upcoming'
        with st.container(border=True):
            st.write(f"**{c['name']}** — {c['company']} · {status} · {c['next_followup']}")
            st.caption(f"{c['status']} · Last outreach: {c['last_contact'] or 'not recorded'}")
            st.link_button('View profile', c['linkedin_url'])
st.divider()
st.caption('Local SQLite storage; cloud filesystem is not persistent. No third-party API calls for search or writing, and no LinkedIn automation.')
