from fastapi import FastAPI

from app.routers import decision, questions

app = FastAPI(title="Rule Based Engine")

app.include_router(questions.router)
app.include_router(decision.router)
