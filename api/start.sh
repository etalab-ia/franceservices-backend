#! /usr/bin/env bash

PYTHONPATH=. alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8090 --log-level debug
