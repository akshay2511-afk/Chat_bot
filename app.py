from fastapi import FastAPI

from routes.apis import router


app = FastAPI(title="Rasa ↔ FastAPI Bridge")

app.include_router(router)

