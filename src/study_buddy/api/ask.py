from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from study_buddy.models import Answer
from study_buddy.qa.pipeline import answer_question

router = APIRouter(tags=["ask"])


class AskRequest(BaseModel):
    """The JSON body Streamlit sends: {"question": "..."}."""

    question: str = Field(min_length=1)


# plain def, not async: the chain waits for Grunden, LanceDB, Postgres and the
# model, so FastAPI runs this in a thread of its own
@router.post("/ask")
def ask(request: AskRequest) -> Answer:
    try:
        return answer_question(request.question)
    except ValueError as error:
        # a question with only spaces passes min_length, retrieve() refuses it
        raise HTTPException(status_code=400, detail=str(error)) from error
