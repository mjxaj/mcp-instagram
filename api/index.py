from server import app as fastapi_app
from fastapi import Request
from mangum import Mangum

handler = Mangum(fastapi_app)
