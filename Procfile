web: uvicorn app:app --host 0.0.0.0 --port 8000
rasa: rasa run --enable-api --cors "*" --port 5005
actions: rasa run actions --actions actions.actions --port 5055
