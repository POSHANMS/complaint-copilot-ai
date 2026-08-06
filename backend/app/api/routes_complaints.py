from fastapi import APIRouter

router = APIRouter(prefix="/complaints", tags=["Complaints"])

@router.get("/")
async def list_complaints():
    return {"message": "Complaints CRUD endpoint placeholder"}
