from pathlib import Path
from typing import Optional

import yaml
from fastapi import FastAPI, HTTPException, Query

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

app = FastAPI(title="Rule Based Engine")


@app.get("/api/questions")
def get_questions(state: Optional[str] = Query(None, description="State identifier, e.g. 'california'")):
    if not state:
        raise HTTPException(status_code=400, detail="Query parameter 'state' is required")

    questions_file = CONFIG_DIR / state.lower() / "questions.yaml"
    if not questions_file.is_file():
        raise HTTPException(status_code=404, detail=f"No questions found for state '{state}'")

    with questions_file.open() as f:
        return yaml.safe_load(f)
