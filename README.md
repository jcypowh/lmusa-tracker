# LMUSA Practice Tracker

A simple tracker for post-lesson practice improvement, built for Jeremy (student) and
Darren Deng (teacher). Each piece has "areas of improvement" that are color-coded:

- **Green** — good / mastered
- **Orange** — working on
- **Blue** — problematic, needs attention

Workflow: Darren logs an area of improvement (with notes, optionally tied to a lesson
video). Jeremy uploads a practice video responding to it. Either side can leave comments
on that area (Jeremy can ask questions, Darren can give feedback), and the thread keeps a
running history so nothing said in a lesson gets forgotten. Status is updated as things
move from blue -> orange -> green.

There's no password login — you just pick "Darren" or "Jeremy" on the landing page.

## Running locally

```
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000

## Deploying to Railway

1. Push this folder to a GitHub repo and connect it to a new Railway project (or use the
   Railway CLI).
2. In the Railway service, add a **Volume** (Settings -> Volumes) and mount it at `/data`.
3. Set these environment variables on the service:
   - `UPLOAD_DIR=/data/uploads`
   - `DATABASE_PATH=/data/lmusa.db`
   - `SECRET_KEY=<some random string>`
4. Railway will detect the `Procfile` and run `gunicorn app:app`. Deploy.

Because videos and the SQLite database both live on the mounted volume, they survive
redeploys. If the video library grows large over time, moving video storage to an object
store (Cloudflare R2 / S3) is the natural next step — the `save_video`/`uploaded_file`
functions in `app.py` are the only places that would need to change.

## Adding the rest of the pieces

The Rachmaninoff Prelude in G minor (Op. 23 No. 5) is seeded by default. Add the other
four from the "Pieces" page directly in the app.
