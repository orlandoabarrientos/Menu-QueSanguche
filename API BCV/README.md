# BCV Sheets

Backend en FastAPI que obtiene las tasas oficiales del BCV (USD/EUR) y las actualiza en un Google Sheet diariamente a las 00:00 (hora Venezuela).

## Requisitos
- Python 3.13+
- Credenciales de Service Account para Google Sheets (JSON)

## Instalación
```bash
pip install -r requirements.txt
```

## Variables de entorno
- `GOOGLE_APPLICATION_CREDENTIALS`: Ruta al JSON del Service Account
- `GOOGLE_SHEET_ID`: ID del Sheet destino
- `GOOGLE_SHEET_TAB`: Nombre de la pestaña (default: Hoja 1)
- `GOOGLE_SHEET_RANGE`: Rango a actualizar (default: A2:B2)
- `GOOGLE_SHEET_MODE`: `update` o `append` (default: update)
- `BCV_VERIFY`: `true`/`false` para verificación SSL (default: true)

## Uso
Ejecuta la API:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Endpoints:
- `GET /rates`
- `GET /rates/{currency_code}`

## Programación diaria
El scheduler interno ejecuta la actualización del Sheet a las 00:00 (America/Caracas).

## Notas
- Comparte el Sheet con el correo del Service Account.
- No subas el JSON de credenciales al repositorio.
