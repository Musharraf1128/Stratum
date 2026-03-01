from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from stratum.api.routes import router, set_workflow


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import and execute demo_workflow to register agents + build the graph
    from stratum.core.agent import clear_registry
    from demo_workflow import build_workflow  # registers agents via @agent decorators

    wf = build_workflow()
    set_workflow(wf)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Stratum API",
        description="Graph-native execution control layer for multi-agent systems.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    return app


app = create_app()
