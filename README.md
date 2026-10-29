# Networking Outreach Agent MVP

A local Streamlit dashboard to manage career networking and coffee chats. Stores contact information in SQLite, ranks relevance using a transparent 100-point rubric, generates editable outreach drafts (AI optional), tracks outreach stages, and suggests follow-up dates.

## Run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Visit the local URL printed by Streamlit, normally `http://localhost:8501`. Click **Add example: Darrian Mankin** to test the app. The example uses only the profile screenshot supplied by the user; Northwestern *employment* is not treated as proof of alumni status.

## Enable AI drafting (optional)

Set `OPENAI_API_KEY` in your terminal, or paste it in the sidebar. For example:

```bash
export OPENAI_API_KEY='your_api_key_here'
streamlit run app.py
```

You can set `OPENAI_MODEL` to another model your API account supports. Without an API key, editable starter drafts are available. OpenAI API use may incur charges. Don't commit real API keys or the SQLite database.

## Workflow

1. Add a person's LinkedIn URL and *manually verified* background details; the app **does not fetch or scrape their LinkedIn profile**.
2. Review the deterministic score, based on user-selected factors.
3. Generate/edit a connection invitation and save it.
4. Open the profile and manually send the invitation, then record **Invitation sent**.
5. After the person accepts, record **Connected** and draft a coffee chat request.
6. Record **Coffee chat requested**, **Replied**, or **Scheduled**. Suggested reminders appear in the Follow-ups tab.
7. Export CRM rows to CSV for backups or analysis.

## Scoring

- Fintech domain: 25 points
- Current PM role: 25 points
- Verified shared university: 20 points
- Relevant career transition: 20 points
- Verified alumni/community connection: 10 points

These are independently chosen and can overlap, so review before enabling multiple flags. No demographic inference, automatic scraping, connection sending, or DM automation is performed.

## Architecture

- `app.py`: Streamlit interface
- `core.py`: SQLite database, scoring, message generation, and follow-up rules
- `tests/`: unit tests

All outreach needs human approval. Follow-up dates are informational and do not trigger messages or background jobs. Current prototype has one local user, no authentication, and is not suitable as a public multiuser deployment without additional access control, encryption, and privacy review.

## Candidate discovery (v2)

The **Discover candidates** tab now supports two research workflows:

1. **Public-web discovery:** Set up a [Brave Search API](https://api.search.brave.com/) key, enter it in the sidebar (or set `BRAVE_SEARCH_API_KEY`), select companies/roles/schools, and run a limited number of searches. Search results come from independently hosted public pages, excluding LinkedIn domains. The app stores citations and search snippets as **unverified leads** in `discovery_leads`; research each page, enter verified name/company/role, mark as Verified, and promote to the CRM using a LinkedIn URL you found manually and verified scoring checkboxes. Search API usage may have fees and rate limits. No search call runs until you press Search.
2. **Manual LinkedIn-assisted review:** You browse LinkedIn yourself and enter a profile URL, name, role and relevant facts in the Streamlit app. No extension, automation, cookies, session sharing, or LinkedIn crawling.

The discovery system searches for *potentially relevant pages*, not guaranteed unique people. It does not infer contact details or guarantee employer accuracy. Every contact requires your verification. Candidate scoring remains transparent and human-verified. The application does not read your logged-in LinkedIn browser session, and does not automate connection requests, direct messages, or follow-ups.

### Current limitations

Search results are dependent on Brave Search API access, indexing, and query quality; some will be false positives, news articles, or unrelated pages. LinkedIn profiles are not automatically fetched. The scoring is deterministic based on user-verified checkboxes; it is not yet learned from successful chats. Source excerpts may be outdated; cross-check before outreach.
