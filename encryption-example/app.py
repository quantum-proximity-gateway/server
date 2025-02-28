from litestar import Litestar, get, post
import oqs


@get('/')
async def hello_world() -> str:
    return 'Hello, world!'


app = Litestar(
    route_handlers=[
        hello_world,
    ],
    debug=True
)