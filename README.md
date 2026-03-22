# SpriteForge v1

SpriteForge is a personal project for my own 2D game asset workflow.

The goal is simple: take a reference image, run it through a lightweight local pipeline, and get back usable pixel art outputs without turning the project into a bloated platform. This repository is intentionally scoped as a practical, local-first foundation that I can run on my own machine, extend over time, and use while building portfolio or hobby games.

This v1 scaffold includes:

- `frontend/`: a small Next.js App Router UI for upload, polling, preview, and download
- `backend/`: a FastAPI backend with SQLite, Celery, Redis, local storage, manifest output, and provider wiring
- `MockImageProvider`: a fully runnable local provider for end-to-end testing without paid API calls
- `GeminiImageProvider`: a backend-only scaffold behind the same interface for later experimentation

## Folder structure

```text
.
├── backend
│   ├── app
│   │   ├── api
│   │   ├── core
│   │   ├── db
│   │   ├── models
│   │   ├── repositories
│   │   ├── schemas
│   │   ├── services
│   │   │   └── providers
│   │   └── tasks
│   ├── requirements.txt
│   └── storage
├── frontend
│   ├── package.json
│   └── src
│       ├── app
│       ├── components
│       └── lib
└── .env.example
```

## Project direction

This is not meant to be a SaaS app or a general AI image toy.

It is a focused tool for a personal game-art workflow:

- upload a reference image
- choose `character`, `object`, or `auto`
- run an async job
- get back either an 8-direction character set or a single object sprite
- inspect the result and download a ZIP

For v1, the emphasis is on:

- usable outputs
- clean engineering structure
- local development
- easy iteration

It intentionally does not include auth, billing, cloud storage, accounts, or multi-tenant platform concerns.

## Architecture decisions

- FastAPI owns uploads, job metadata, local storage paths, manifest reads, ZIP download, and static file serving.
- Celery owns the async generation pipeline and updates explicit job `status` and `stage` values in SQLite.
- The provider interface isolates classification, structured summary extraction, and generation so I can swap providers later without reshaping the app.
- Local filesystem storage is deterministic by `job_id`, with separate reference, raw output, final output, manifest, and ZIP paths.
- Pillow is used only for lightweight mechanical normalization, centering, transparency preservation, and mock placeholder output generation.

## Local setup

### 1. Install and start Redis locally

SpriteForge expects Redis to be running at `redis://localhost:6379/0` by default.

If you do not already have Redis installed, install it with your system package manager. For example, on macOS with Homebrew:

```bash
brew install redis
brew services start redis
```

You can verify it is running with:

```bash
redis-cli ping
```

You should see:

```text
PONG
```

### 2. Configure environment variables

Copy the example values:

```bash
cp .env.example backend/.env
cp .env.example frontend/.env.local
```

`backend/.env` can keep the default values for local development. `frontend/.env.local` only needs:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 3. Run the backend API

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### 4. Run the Celery worker

In a second terminal:

```bash
cd backend
source .venv/bin/activate
celery -A app.tasks.celery_app.celery_app worker --loglevel=info
```

### 5. Run the frontend

In a third terminal:

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:3000`.

## v1 flow

1. Upload a reference image.
2. Choose `character`, `object`, or `auto`.
3. Submit the job.
4. FastAPI stores the upload and creates a SQLite job row.
5. Celery picks up the job and runs staged processing.
6. The provider classifies `auto` jobs, summarizes the reference, and generates assets.
7. Pillow performs tiny mechanical cleanup and normalization to the target size.
8. The worker writes `manifest.json`, packages a ZIP, and marks the job complete.
9. The frontend polls until complete, then renders previews and a download button.

## Storage layout

Generated files are stored locally under `backend/storage/`:

```text
storage/
├── references/{job_id}/reference.png
└── outputs/{job_id}/
    ├── raw/
    ├── final/
    ├── manifest.json
    └── spriteforge_{job_id}.zip
```

Character outputs use:

- `front.png`
- `back.png`
- `left.png`
- `right.png`
- `front_left.png`
- `front_right.png`
- `back_left.png`
- `back_right.png`

Object outputs use:

- `object.png`

Uploads are limited to:

- `.png`
- `.jpg`
- `.jpeg`

## Why this setup exists

I wanted something that feels like a real software project, but still stays lean:

- the frontend is only responsible for the user flow
- the API is responsible for persistence and file access
- the worker is responsible for staged processing
- storage stays local and predictable
- the provider layer stays swappable

That gives me a solid base to build on without overengineering a one-person tool.

## Provider notes

### Mock provider

- Fully runnable today
- Uses deterministic heuristics for `auto` classification
- Generates placeholder structured summaries
- Produces valid PNG outputs in the exact final file structure
- Reuses the uploaded reference image as the consistent base for all generated directions

### Gemini scaffold

- Kept backend-only
- Reads credentials from environment variables
- Isolated behind the same provider interface
- Marked as scaffolded and not yet fully implemented

## API routes

- `POST /api/v1/jobs`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs/{job_id}/results`
- `GET /api/v1/jobs/{job_id}/download`
- `GET /api/v1/health`

## Notes

- This v1 intentionally avoids auth, billing, cloud storage, advanced repair pipelines, animation, tilesets, and browser editing.
- The default provider is `mock` so the app is usable without any external AI service.
- The current scope is personal-use first: something I can run locally, improve gradually, and use in my own asset workflow.
