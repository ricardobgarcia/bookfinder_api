from mangum import Mangum

from src.bookfinder_api.main import app

handler = Mangum(app)
