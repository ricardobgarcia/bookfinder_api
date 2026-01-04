from datetime import datetime

from fastapi import APIRouter, Request

from ....core.ingestion.scraper import get_csv_status


router = APIRouter(tags=['health'])


@router.get('/health')
def health(request: Request):
    now = datetime.now()
    csv_status = get_csv_status()
    books_cache = getattr(request.app.state, 'books_cache', [])

    return {
        'status': 'ok',
        'time': now.isoformat(),
        'message': f'BookFinder API is healthy at {now:%Y-%m-%d %H:%M:%S}',
        'csv_status': {
            'exists': csv_status['exists'],
            'is_fresh': csv_status['is_fresh'],
            'last_updated': (
                csv_status['last_updated'].isoformat()
                if csv_status['last_updated']
                else None
            ),
            'age_seconds': csv_status['age_seconds'],
        },
        'total_books_in_cache': len(books_cache),
    }
