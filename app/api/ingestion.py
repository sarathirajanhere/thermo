from fastapi import APIRouter, HTTPException, UploadFile

from app.services.ingestion_service import ingest_csv_bytes, ingest_json_bytes

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/upload")
async def upload_thermal_data(file: UploadFile):
    """
    Accept a local CSV or JSON file of FIRMS-compatible thermal records
    and load it into the event store. This is the "ingestion" entry
    point mentioned in the shared architecture — it deliberately does
    NOT call the live NASA FIRMS API, to keep the MVP working offline.
    """
    contents = await file.read()
    filename = (file.filename or "").lower()

    try:
        if filename.endswith(".json"):
            result = ingest_json_bytes(contents)
        elif filename.endswith(".csv"):
            result = ingest_csv_bytes(contents)
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Upload a .csv or .json file.",
            )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {exc}")

    return {
        "filename": file.filename,
        "ingested_count": len(result["ingested"]),
        "ingested_ids": result["ingested"],
        "errors": result["errors"],
    }
