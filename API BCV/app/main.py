from __future__ import annotations

import logging
import os
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .scraper import BCV_URL, ScraperError, get_bcv_rates
from .sheets import update_bcv_sheet

app = FastAPI(title="BCV Exchange Rates", version="1.0.0")
_LOGGER = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _parse_verify_setting() -> bool | str:
    value = os.getenv("BCV_VERIFY", "false").strip().lower()
    if value in {"0", "false", "no"}:
        return False
    if value in {"1", "true", "yes"}:
        return True
    return value


def _scheduled_refresh() -> None:
    verify = _parse_verify_setting()
    try:
        rates = get_bcv_rates(verify=verify)
    except ScraperError as exc:
        _LOGGER.error("Scraper error (scheduled): %s", exc)
        return
    _LOGGER.info("Tasas BCV actualizadas: %s", rates)
    try:
        update_bcv_sheet(rates)
    except Exception as exc:
        _LOGGER.error("Error actualizando Google Sheets: %s", exc)


# @app.on_event("startup")
# async def start_scheduler() -> None:
#     scheduler = AsyncIOScheduler(timezone=ZoneInfo("America/Caracas"))
#     scheduler.add_job(
#         _scheduled_refresh,
#         CronTrigger(hour=0, minute=0),
#         id="bcv_daily_refresh",
#         replace_existing=True,
#     )
#     scheduler.start()
#     app.state.scheduler = scheduler


# @app.on_event("shutdown")
# async def shutdown_scheduler() -> None:
#     scheduler = getattr(app.state, "scheduler", None)
#     if scheduler:
#         scheduler.shutdown(wait=False)


@app.get("/", tags=["health"])
async def read_root():
    return {"status": "ok", "service": "bcv-api"}


@app.get("/rates", tags=["rates"])
async def read_rates():
    try:
        rates = get_bcv_rates(verify=_parse_verify_setting())
    except ScraperError as exc:
        _LOGGER.error("Scraper error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"source": BCV_URL, "rates": rates}


@app.get("/rates/{currency_code}", tags=["rates"])
async def read_rate(currency_code: str):
    code = currency_code.lower()
    try:
        rates = get_bcv_rates([code], verify=_parse_verify_setting())
    except ScraperError as exc:
        _LOGGER.error("Scraper error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if code not in rates:
        raise HTTPException(status_code=404, detail=f"Currency '{currency_code}' not available")
    return {"source": BCV_URL, "currency": code, "value": rates[code]}
