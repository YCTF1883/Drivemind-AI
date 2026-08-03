# DriveMind AI

DriveMind AI is an AI-assisted R&D operations management platform for enterprise development teams.

It focuses on a complete business workflow:

```text
Project creation
↓
AI-assisted task breakdown
↓
Task assignment
↓
Employee progress report
↓
AI report analysis
↓
Task / project progress update
↓
Manager project Q&A
```

## Highlights

- Project management for R&D teams.
- Task assignment with employee-specific task visibility.
- Work reports for progress, blockers, risks, and support requests.
- AI-assisted task breakdown and report analysis powered by DeepSeek API.
- Manager Q&A for project status and risk tracking.
- RBAC, dynamic menus, JWT authentication, and API-level permission control.
- FastAPI + Vue 3 + Naive UI + MySQL full-stack implementation.

## Tech Stack

Backend:

- Python 3.11
- FastAPI
- Tortoise ORM
- MySQL / asyncmy
- Pydantic v2
- LangGraph
- DeepSeek API

Frontend:

- Vue 3
- Vite
- Naive UI
- Pinia
- Vue Router
- Axios

## Local Setup

### Backend

```bash
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Fill `.env` with local database settings and optional DeepSeek API settings. Do not commit `.env` to GitHub.

### Frontend

```bash
cd web
npm install
npm run dev
```

## Default Development Account

```text
username: admin
password: 123456
```

Change the default password before deploying to any public environment.

## License and Attribution

This project is built on top of [vue-fastapi-admin](https://github.com/mizhexiaoxiao/vue-fastapi-admin), which is licensed under the MIT License. The original copyright and license notice are preserved as required by the MIT License.

DriveMind AI adds and restructures the R&D operations business modules, AI workflows, DeepSeek integration, project/task/report collaboration flow, and related frontend pages.

See [LICENSE](LICENSE) for details.
