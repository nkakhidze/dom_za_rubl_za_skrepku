from fastapi import APIRouter

router = APIRouter(
    prefix="/public",
    tags=["public"],
)


@router.get("/exchange-chain")
def get_exchange_chain():
    return []