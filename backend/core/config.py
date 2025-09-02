import os
from pydantic import BaseModel

class Settings(BaseModel):
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:123456@localhost:5432/PAN",
    )

settings = Settings()
