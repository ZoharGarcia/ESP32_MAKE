# IoT Make + Telegram + ESP32 on Render (FastAPI + PostgreSQL)

API simple para enviar/leer comandos `cool_on/cool_off` por `device_id`. 
Pensada para integrarse con **Make (Integromat)** y controlar un **ESP32** que simula enfriamiento con un LED.
- **ESP32**: envía telemetría a Make (webhook) y consulta `GET /device/{id}/command`.
- **Make**: si hay alerta → Telegram; si dices "enfriar"/"apagar" en Telegram → `POST /device/{id}/command`.
- **Render**: aloja FastAPI + PostgreSQL (persistente).

## Estructura
```
main.py               # FastAPI + SQLAlchemy (Postgres)
requirements.txt
render.yaml           # Infra: web service + DB (plan free)
.env.example
firmware/
  esp32/
    esp32_dht_demo.ino
```

## Deploy en Render (click-to-deploy)

1. Sube este repo a GitHub.
2. En Render, crea un **New +** → **Blueprint** y selecciona tu repo (usa `render.yaml`).
3. Render creará:
   - **Web Service** (Python) con start: `gunicorn -k uvicorn.workers.UvicornWorker -w 1 main:app`
   - **PostgreSQL** (plan free) y pondrá `DATABASE_URL` en el servicio.
4. En el servicio web, agrega (opcional) variable **API_KEY** para proteger el `POST`.
5. Espera a que se construya. Tu URL será algo como: `https://iot-command-api.onrender.com`

### Endpoints
- `GET  /health`
- `GET  /device/<id>/command`
- `POST /device/<id>/command`
  - Headers opcionales: `x-api-key: <API_KEY>`
  - Body: `{"command":"cool_on"}` o `"cool_off"`

### Pruebas rápidas
```bash
curl https://<tu-servicio>.onrender.com/health

curl https://<tu-servicio>.onrender.com/device/esp32-demo-01/command

curl -X POST https://<tu-servicio>.onrender.com/device/esp32-demo-01/command   -H "Content-Type: application/json"   -H "x-api-key: supersecretkey"   -d '{"command":"cool_on"}'
```

## Make (Integromat)

**Escenario A — Webhook → Telegram (alerta)**
1. Crea **Custom Webhook**; copia su URL.
2. Filtro: `temp >= 30` (o el umbral que definas).
3. **Telegram Bot → Send a message** con la alerta.

**Escenario B — Telegram → HTTP POST (comando)**
1. **Telegram Bot → Watch updates**.
2. **Router** con 2 rutas:
   - Si mensaje contiene `enfriar` → `POST https://<tu-servicio>.onrender.com/device/esp32-demo-01/command` con `{"command":"cool_on"}`.
   - Si mensaje contiene `apagar` → igual con `cool_off`.
3. (Opcional) Responde con “✅ activado” / “🛑 desactivado”.

## Firmware ESP32 (Arduino)
Abre `firmware/esp32/esp32_dht_demo.ino` y configura:
- `WIFI_SSID`, `WIFI_PASS`
- `API_BASE = "https://<tu-servicio>.onrender.com"`
- `DEVICE_ID = "esp32-demo-01"`
- `API_KEY` (si la definiste en Render)
- `MAKE_WEBHOOK_URL` (el del escenario A)

**Librerías**: `DHT sensor library` (Adafruit), `Adafruit Unified Sensor`

## Seguridad
- Mantén secreto el Webhook de Make.
- Usa API_KEY para los POST.
- PostgreSQL gestionado por Render (credenciales env); no subas `.env` al repo.
