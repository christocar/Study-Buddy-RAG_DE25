from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import RequestBlocked

from study_buddy.ingestion.loaders.youtube import load_youtube
from study_buddy.ingestion.pipeline import ingest_document

router = APIRouter(tags=["youtube"])


class YouTubeRequests(BaseModel):
    """
    The JSON body: {"url": "https://youtu.be/....."}
    """

    url: str


# Normal def - the loader and the pipeline block so FastAPI runs this in a thread.
@router.post("/youtube")
def youtube(request: YouTubeRequests) -> dict[str, int | str]:
    try:
        # Loader fetches transcript, our pipeline does the rest
        document = load_youtube(request.url)
        document_id = ingest_document(document)
    except RequestBlocked as error:
        # Youtue blocks our IP for a while, if that happens:
        # DO NOT RUN SEVERAL TIMES, instead just wait for a while.
        raise HTTPException(
            status_code=503,
            detail="Youtube is blocking our requests from this server. Try again later!",
        ) from error
    except ValueError as error:
        # Not a YT link, no usable transcript OR contains too little text
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {"document_id": document_id, "filename": document.filename}
