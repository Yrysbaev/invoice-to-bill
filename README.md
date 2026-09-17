# Invoice → Bill

A small local web app that reads **vendor invoice PDFs**, extracts the data with
Claude, lets a human review and edit it, and creates a **Bill** in **QuickBooks
Online**.

This fills a specific gap: some QuickBooks connectors can create *invoices* and
*estimates* but **not vendor Bills** — this app does exactly that.

## How it works (target flow)

```
Upload PDF
   → Extract text (pdfplumber)
   → Claude parses vendor / dates / line items into structured JSON
   → Human reviews & edits on a form
   → Confirm
   → POST to QuickBooks  /v3/company/{realmId}/bill
```

## Tech stack

- **Python / Flask** — web app
- **QuickBooks Online REST API** — OAuth2 authorization-code flow, Bill creation
- **Anthropic API (Claude)** — parse invoice text into structured JSON
- **pdfplumber** — PDF text extraction

## Project layout

```
invoice-to-bill/
├── run.py                 # entrypoint — starts the Flask dev server
├── app/
│   ├── __init__.py        # Flask app factory
│   ├── config.py          # loads configuration from environment
│   ├── routes.py          # HTTP routes (just a landing page for now)
│   ├── templates/
│   │   └── index.html     # landing page
│   └── static/            # css/js/assets
├── uploads/               # uploaded PDFs (git-ignored)
├── requirements.txt
├── .env.example           # copy to .env and fill in
└── README.md
```

## Getting started

### 1. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Then edit `.env` and fill in:

| Variable            | What it is |
|---------------------|------------|
| `QB_CLIENT_ID`      | QuickBooks app client id (developer.intuit.com → Keys & OAuth) |
| `QB_CLIENT_SECRET`  | QuickBooks app client secret |
| `QB_REDIRECT_URI`   | OAuth redirect URI, must match the Intuit portal exactly (e.g. `http://localhost:5000/callback`) |
| `QB_ENVIRONMENT`    | `sandbox` or `production` |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude |

### 3. Run the app

```bash
python run.py
```

Open <http://localhost:5000>.

## Roadmap (milestones)

1. **Repo skeleton** — structure, README, `.gitignore`, `requirements.txt`,
   `.env.example`. *(this milestone — no business logic yet)*
2. **QuickBooks OAuth** — `/connect` and `/callback` routes, token storage with
   refresh.
3. **PDF upload + Claude extraction** — parse invoice into structured JSON.
4. **Review / edit screen** — pull real vendors and expense accounts from
   QuickBooks, match/create vendor, assign an account per line item.
5. **Submit** — create the actual Bill via the QuickBooks API.
6. **Polish** — error handling, a couple of basic tests, deploy/run notes.
