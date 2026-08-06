from fastapi import APIRouter

router = APIRouter(prefix="/complaints", tags=["Extraction"])

@router.post("/extract")
async def extract_complaint():
    return {"message": "LangGraph extraction endpoint placeholder"}
