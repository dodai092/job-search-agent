# Deploying the Sheet append endpoint

This is a one-time manual step — Google requires you to authorize this
yourself, I can't do it from here.

1. Open the Sheet: https://docs.google.com/spreadsheets/d/1dlUJHWRtPm39wcWeTg5p54T_Cic7lOQl2rUH_WUh1jU/edit
2. **Extensions → Apps Script**
3. Delete whatever's in `Code.gs` by default, paste in the contents of
   `Code.gs` from this folder.
4. **Project Settings** (gear icon, left sidebar) → **Script Properties** →
   **Add script property**:
   - Property: `SHARED_SECRET`
   - Value: any random string (e.g. `openssl rand -hex 16`) — not a real
     password, just stops random internet traffic from writing to your
     sheet. **Not written here or anywhere in this repo** — keep the actual
     value in your own notes/password manager and pass it to the daily
     routine as the `SHEET_APPEND_SECRET` env var (see
     `scripts/append_to_sheet.py`), same pattern as your Vinalia Evidencija
     setup.
5. **Deploy → New deployment**:
   - Type: **Web app**
   - Execute as: **Me**
   - Who has access: **Anyone** (authorization is via the shared secret
     above, not Google's access control — "Anyone" here just means Google
     won't block the HTTP request before it reaches the script)
6. Click **Deploy**, authorize the permissions prompt (it needs access to
   this one spreadsheet).
7. Copy the **Web app URL** it gives you (ends in `/exec`) and send it back
   to me — I'll save it into the project config so the daily pull can use it.

## What it does

A single `doPost` endpoint that appends rows to the Sheet. Nothing else —
no read access, no delete, no way to touch any other file. Existing rows
and your manual Status edits are never touched, since it only calls
`appendRow()`.
