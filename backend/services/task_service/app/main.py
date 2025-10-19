from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app_common.logging import configure_logging, get_logger
from app_common.middleware import CorrelationIdMiddleware

from .routers import ai_recommendations, auth_test, edge, health, internal_catalog, kafka, kpi, kpi_predict, metrics, pantheon, reports, stream, task_analytics, teams, trebovanja, tv, users_simple, worker_picking, worker_team, zaduznice

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="Magacin Task Service", version="0.1.0")
app.add_middleware(CorrelationIdMiddleware)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(auth_test.router, prefix="/api", tags=["auth"])
app.include_router(users_simple.router, prefix="/api", tags=["users"])
app.include_router(metrics.router, prefix="/api", tags=["metrics"])
app.include_router(trebovanja.router, prefix="/api", tags=["trebovanja"])
app.include_router(zaduznice.router, prefix="/api", tags=["zaduznice"])
app.include_router(tv.router, prefix="/api", tags=["tv"])
app.include_router(kpi.router, prefix="/api/kpi", tags=["kpi"])
app.include_router(kpi_predict.router, prefix="/api/kpi", tags=["kpi"])
app.include_router(ai_recommendations.router, prefix="/api/ai", tags=["ai"])
app.include_router(kafka.router, prefix="/api", tags=["kafka"])
app.include_router(stream.router, prefix="/api", tags=["stream"])
app.include_router(teams.router, prefix="/api", tags=["teams"])
app.include_router(edge.router, prefix="/api", tags=["edge"])
app.include_router(internal_catalog.router, tags=["catalog"])
app.include_router(worker_picking.router, prefix="/api", tags=["worker-picking"])
app.include_router(worker_team.router, prefix="/api", tags=["worker-team"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(task_analytics.router, prefix="/api", tags=["task-analytics"])
app.include_router(pantheon.router, prefix="/api", tags=["pantheon"])

Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("task-service.startup")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("task-service.shutdown")
