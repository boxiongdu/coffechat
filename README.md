# Networking Outreach Agent MVP

A local Streamlit dashboard to manage career networking and coffee chats. Stores contact information in SQLite, ranks relevance using a transparent 100-point rubric, generates editable template-based outreach drafts, tracks outreach stages, and suggests follow-up dates.

## Run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Visit the local URL printed by Streamlit, normally `http://localhost:8501`. Click **Add example: Darrian Mankin** to test the app. The example uses only the profile screenshot supplied by the user; Northwestern *employment* is not treated as proof of alumni status.

## No API keys needed

Message drafts use local templates and your manually verified profile details. Public-web search links open in your own browser; save relevant page URLs and evidence into the research inbox.

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

## Candidate discovery (v3, no API keys)

1. **Public-web discovery:** Pick target companies, roles and schools, then open the suggested Google searches manually. Review independently published biographies and save the HTTPS page URL, title, and relevant notes in the research inbox. Verify the person's identity, role, and company before promoting them into CRM.
2. **LinkedIn-assisted review:** Browse LinkedIn yourself and paste the profile URL and verified career details into the app. The app never reads a logged-in LinkedIn session and never sends invitations or DMs.
3. **Offline message generation:** Draft editable connection and coffee-chat messages from the contact's verified fields. No OpenAI account or usage tokens required.

**Deployment caution:** The app still uses SQLite; a file committed to GitHub is not durable writable cloud storage. Streamlit Community Cloud may lose database writes after restarts. Restrict app access, and migrate to persistent storage before relying on it for real contact records.

No automated search, scraping, invitations, or follow-ups.
