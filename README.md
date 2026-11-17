# Flask Blog

A full-featured blog built with Flask, SQLAlchemy, Flask-Migrate, Flask-Login and Flask-WTF.

## Features
- Registration, login, logout, remember-me sessions, change password, edit profile (Flask-Login)
- Blog posts CRUD with a rich-text editor (Quill), tags, reading time, related posts
- Comments (logged-in users), delete by comment author or post author
- Search (title/content), tag filter, pagination, popular tags
- Profile pages, dark mode, responsive Bootstrap 5 UI
- CSRF protection, password hashing, HTML sanitising (XSS-safe), security headers, error pages
- 27 unit tests (pytest), Docker + Gunicorn, `/health` endpoint

## Run locally
```
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Windows: copy .env.example .env
flask --app wsgi db upgrade       # creates the database
flask --app wsgi seed             # OPTIONAL: demo data (demo@example.com / demo1234)
flask --app wsgi run --debug      # http://127.0.0.1:5000
```

## Tests
```
pytest -v
```

## Docker
```
docker compose up --build         # http://localhost:8000
```

## Project structure
```
app/            application package (factory in __init__.py)
  auth/         login, register, settings Blueprint
  main/         posts, comments, search, profile Blueprint
  templates/    Jinja2 templates      static/  CSS
migrations/     Flask-Migrate (Alembic) versions
tests/          pytest suite
```

## Changing models later
```
flask --app wsgi db migrate -m "describe change"
flask --app wsgi db upgrade
```
