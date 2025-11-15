# Face Recognition Attendance

This project is a face recognition based attendance system with: registration, training, live attendance, an optional Tkinter GUI, and a simple Flask web dashboard.

Quick notes:
- Run `python flask_face_attendance_app.py` to start the dashboard (this file expects `register.py`, `train.py`, `attendance.py`, and `db.py` in the project root).
- The project uses a MySQL database (update `db.py` configuration or set environment variables if you prefer).
- Email sending reads SMTP credentials from environment variables (`SMTP_USER`/`SMTP_APP_PASSWORD`).

Preparations for GitHub deployment
- Add a `.gitignore` (provided)
- Add a `.env` locally for development using `.env.example`
- Remove or rotate any hard-coded credentials before pushing

Deployment options
- Heroku / Render: use `Procfile` (already present) and push the repo; set required env vars through the provider UI.
- GitHub Actions + server: create a workflow that builds a Python environment and deploys.

Local development
1. Create and activate a virtualenv

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill credentials
3. Initialize DB (if using MySQL/XAMPP) then run

```powershell
python db.py
python flask_face_attendance_app.py
```

Security
- Do not commit `.env` or any credentials. Use environment variables in production.

If you want, I can:
- Initialize a git repo, create commits, and push to a GitHub repository (you must provide a GitHub repo name or authorize `gh` usage)
- Create a GitHub Actions workflow to automatically deploy to Heroku or Render
- Add a lightweight Dockerfile for containerized deployment

What would you like me to do next? (I can push to GitHub and set up deployment.)