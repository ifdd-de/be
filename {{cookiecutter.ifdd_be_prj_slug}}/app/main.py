"""Application entry point.

The application is assembled by ifdd.be.core. Instance-specific endpoints are added
through the routers registered below.
"""

from ifdd.be.core import create_app

from app.routers import instance_routers
from app.settings import settings

app = create_app(settings, extra_routers=instance_routers)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.IFDD_BE_HOST,
        port=settings.IFDD_BE_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        server_header=False,
        workers=settings.MAX_WORKERS,
        access_log=True,
    )
