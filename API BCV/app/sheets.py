from __future__ import annotations

import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread

_LOGGER = logging.getLogger(__name__)


def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def _get_credentials_path() -> str | None:
    return _get_env("GOOGLE_APPLICATION_CREDENTIALS") or _get_env("GOOGLE_SHEETS_CREDENTIALS")


def update_bcv_sheet(rates: dict[str, float]) -> None:
    sheet_id = _get_env("GOOGLE_SHEET_ID", "1-LfjJV6VKgXm-U8QO-3LqGmpetfHU997A_ds5mX2Ai8")
    tab_name = _get_env("GOOGLE_SHEET_TAB", "Hoja 1")
    target_range = _get_env("GOOGLE_SHEET_RANGE", "A2:B2")
    mode = (_get_env("GOOGLE_SHEET_MODE", "update") or "update").lower()
    creds_path = _get_credentials_path()

    if not sheet_id or not creds_path:
        _LOGGER.warning("Google Sheets no configurado. Faltan GOOGLE_SHEET_ID o credenciales.")
        return

    client = gspread.service_account(filename=creds_path)
    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.worksheet(tab_name)

    tz = ZoneInfo("America/Caracas")
    now = datetime.now(tz)
    usd_value = rates.get("usd")
    eur_value = rates.get("eur")
    usd_rounded = round(usd_value, 2) if usd_value is not None else None
    eur_rounded = round(eur_value, 2) if eur_value is not None else None
    row = [now.isoformat(), usd_rounded, eur_rounded]
    normalized_range = target_range.replace("$", "").strip()
    if normalized_range.upper() == "A:A2":
        normalized_range = "A1:A2"

    if mode == "append":
        worksheet.append_row(row, value_input_option="USER_ENTERED")
    else:
        if normalized_range.upper() == "A1:A2":
            worksheet.update(normalized_range, [["USD"], [rates.get("usd")]], value_input_option="USER_ENTERED")
        elif normalized_range.upper() == "A2:B2":
            worksheet.update(normalized_range, [[usd_rounded, eur_rounded]], value_input_option="USER_ENTERED")
        else:
            worksheet.update(normalized_range, [row], value_input_option="USER_ENTERED")

    _LOGGER.info("Google Sheets actualizado (%s).", mode)
