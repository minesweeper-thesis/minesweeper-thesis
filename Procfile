web: alembic -c backend/alembic.ini upgrade head && fastapi run backend/main.py --workers 1 --host 0.0.0.0 --port $PORT
worker: python3 -m backend.jobs.background_generator
