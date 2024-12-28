from litestar import Litestar, get


@get('/')
async def home() -> str:
    return "Hello World!"

app = Litestar([home])