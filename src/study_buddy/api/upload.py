from fastapi import APIRouter, HTTPException, UploadFile

from study_buddy.ingestion.pipeline import ingest_file

router = APIRouter(tags=["upload"])


@router.post("/upload")
async def upload(file: UploadFile) -> dict[str, int | str]:
    content = await file.read()

    try:
        # the pipeline does all the work: load, chunk, embed, save
        document_id = ingest_file(file.filename or "", content)
    except ValueError as error:
        # wrong file type, empty file, not UTF-8... the pipeline says why
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {"document_id": document_id, "filename": file.filename}
