from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import os
import redis

# ---- Redis (Upstash o compatible) ----
# Configura en Vercel:
# REDIS_URL = rediss://... (o redis://)
# REDIS_TOKEN = {token si tu provider lo usa}
REDIS_URL = os.getenv("REDIS_URL")
REDIS_TOKEN = os.getenv("REDIS_TOKEN", None)

if not REDIS_URL:
    raise RuntimeError("REDIS_URL not set")

if REDIS_TOKEN:
    r = redis.Redis.from_url(REDIS_URL, password=REDIS_TOKEN, decode_responses=True, ssl=REDIS_URL.startswith("rediss://"))
else:
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True, ssl=REDIS_URL.startswith("rediss://"))

API_KEY = os.getenv("API_KEY")  #Escribir API_KEY

app = FastAPI(title="Comando API (Vercel)")

class CommandIn(BaseModel):
    command: str  

def key_cmd(device_id: str) -> str:
    return f"cmd:{device_id}"

@app.get("/api/health")
def health():
    return {"ok": True}

@app.get("/api/device/{device_id}/command")
def get_command(device_id: str):
    cmd = r.get(key_cmd(device_id))
    if not cmd:
        # por defecto: Frio
        cmd = "cool_off"
        r.set(key_cmd(device_id), cmd)
    return {"device_id": device_id, "command": cmd}

@app.post("/api/device/{device_id}/command")
def set_command(
    device_id: str,
    body: CommandIn,
    x_api_key: str | None = Header(default=None)
):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")
    if body.command not in ("cool_on", "cool_off"):
        raise HTTPException(status_code=400, detail="invalid command")
    r.set(key_cmd(device_id), body.command)
    return {"ok": True, "device_id": device_id, "command": body.command}
