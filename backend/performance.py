import time
import cProfile
import pstats
import io
from litestar.middleware import DefineMiddleware, MiddlewareProtocol
from litestar.types import ASGIApp, Receive, Scope, Send

class ProfilingMiddleware(MiddlewareProtocol):
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        path = scope.get("path", "")
        
        # Start profiling
        pr = cProfile.Profile()
        pr.enable()
        
        # Start timing
        start_time = time.time()
        
        # Process the request
        await self.app(scope, receive, send)
        
        # End timing
        execution_time = time.time() - start_time
        
        # End profiling
        pr.disable()
        
        # Get profiling results
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Print top 20 functions
        
        print(f"Path: {path} - Execution time: {execution_time:.4f}s")
        print(s.getvalue())