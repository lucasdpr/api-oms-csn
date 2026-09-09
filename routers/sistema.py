from fastapi import APIRouter
from app_core import (
    get_db,
)

router = APIRouter()




@router.get("/", tags=["Sistema"], summary="Verificar se o servidor está no ar")
def root():
    return {"message": "API - Oficina de Moldes CSN Online!"}




@router.get("/api/ping_db", tags=["Sistema"], summary="Verificar conexão com o banco de dados")
def ping_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return {"status": "ok", "banco": "acordado"}
