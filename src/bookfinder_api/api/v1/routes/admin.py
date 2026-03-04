import os
from pydantic import BaseModel

from fastapi import APIRouter, Request, HTTPException, status, Depends


from ....core.auth.jwt import create_access_token
from ....core.auth.or_auth import require_admin_or_cron
from ....core.ingestion.scraper import ensure_books_csv, get_csv_status
from ....core.data.repository import load_books


router = APIRouter(prefix="/admin", tags=["admin"])


class LoginIn(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(body: LoginIn):
    admin_user = os.getenv("ADMIN_USER")
    admin_pass = os.getenv("ADMIN_PASS")

    if body.username == admin_user and body.password == admin_pass:
        token = create_access_token(subject=body.username, role="admin")
        return {"access_token": token, "token_type": "bearer", "role": "admin"}

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@router.post("/scrape", status_code=status.HTTP_201_CREATED)
async def run_scrape(
    request: Request,
    auth_info=Depends(require_admin_or_cron)
):
    """
    Run the scraper to generate/update the database.
    """
    try:
        await ensure_books_csv(force=True)
        request.app.state.books_cache = load_books()
        csv_status = get_csv_status()
        books_cache = request.app.state.books_cache

        return {
            "status": "ok",
            "message": "Scraping finished and CSV updated.",
            "csv_status": {
                "exists": csv_status["exists"],
                "is_fresh": csv_status["is_fresh"],
                "last_updated": (
                    csv_status["last_updated"].isoformat()
                    if csv_status["last_updated"] else None
                ),
                "age_seconds": csv_status["age_seconds"],
            },
            "total_books": len(books_cache),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refresh failed: {type(e).__name__}: {e}",
        )
