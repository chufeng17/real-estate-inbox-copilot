# Real Estate Agent Inbox Copilot

A multi-agent AI system to help real estate agents manage their inbox, leads, and tasks. Built for the Kaggle Agentic Coding Capstone.

> **This repository contains my submission for the Google Agents Intensive Capstone Project.**

## Architecture
- **Backend**: FastAPI (Python)
- **Frontend**: Next.js (TypeScript)
- **Database**: SQLite
- **Agents**: Google Agent Development Kit (Custom Implementation)

## Setup

1.  **Install Backend Dependencies**
    ```bash
    cd backend
    pip install -r requirements.txt
    ```

2.  **Configure Environment**
    Copy `.env.example` to `.env` in the `backend` directory and fill in your API keys.

3.  **Run Backend**
    ```bash
    cd backend
    uvicorn app.main:app --reload
    ```

4.  **Install Frontend Dependencies**
    ```bash
    cd frontend
    npm install
    ```

5.  **Run Frontend**
    ```bash
    cd frontend
    npm run dev
    ```

6.  **Usage**
    - Go to `http://localhost:3000`
    - Login (Register first via API or use default admin/agent if seeded)
    - Click "Sync Emails" to load the sample dataset.

##Demo Reset (Testing Only)

To reset the application to a clean state while preserving user accounts:

```bash
POST /api/v1/admin/reset-demo
Authorization: Bearer <admin_token>
```

This endpoint:
- **Deletes**: All contacts, email threads, email messages, tasks, and embeddings
- **Preserves**: User accounts

**Use for demo/testing only.** Only accessible to admin users (configured via `ADMIN_EMAIL` in settings).

### Testing with Different Datasets

1. Set `DATASET_PATH=./data/sample_emails_initial.json` in `.env`
2. Call `/admin/reset-demo` to clear data
3. Call `/sync/emails` to load initial dataset
4. Test the "before" state

5. Set `DATASET_PATH=./data/sample_emails_after_sync.json`
6. Call `/admin/reset-demo` again
7. Call `/sync/emails` to load updated dataset
8. Test the "after" state with additional emails and tasks
