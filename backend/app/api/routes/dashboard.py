from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_dashboard_data():
    return {"message": "Fila do Dashboard (Em desenvolvimento)"}