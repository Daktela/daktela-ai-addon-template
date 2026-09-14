"""Process entrypoint: `uvicorn server.main:app`.

Kept deliberately tiny - all the wiring lives in `server/app.py`.
"""

import asyncio
import sys

if sys.platform == "win32":
    # Only relevant once you enable persistence. The async Postgres driver
    # (psycopg) cannot run on Windows' default Proactor event loop, and
    # uvicorn picks that one by default. Setting the selector policy before
    # the loop is created avoids a confusing InterfaceError at the first
    # query. Harmless when no database is configured.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from server.app import create_app
from server.di import Container

container = Container()
app = create_app(container)
