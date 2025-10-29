import os
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no identificada")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Tabla Init
def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS commands (
            device_id TEXT PRIMARY KEY,
            command   TEXT NOT NULL
        )
        """))

init_db()

app = FastAPI(title="Control API")

class CommandIn(BaseModel):
    command: str 

@app.get("/health")
def health():
    # DB
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as e:
        return {"ok": False, "db": "down", "error": str(e)}
    return {"ok": True, "db": "up"}

@app.get("/device/{device_id}/command")
def get_command(device_id: str):
    with Session(engine) as s:
        row = s.execute(text("SELECT command FROM commands WHERE device_id=:id"), {"id": device_id}).fetchone()
        if row is None:
            # default value
            cmd = "cool_off"
            s.execute(text("INSERT INTO commands(device_id, command) VALUES (:id, :cmd) ON CONFLICT (device_id) DO NOTHING"),
                      {"id": device_id, "cmd": cmd})
            s.commit()
            return {"device_id": device_id, "command": cmd}
        return {"device_id": device_id, "command": row[0]}

@app.post("/device/{device_id}/command")
def set_command(
    device_id: str,
    body: CommandIn,
    x_api_key: str | None = Header(default=None)
):
    API_KEY = os.getenv("API_KEY")
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")
    if body.command not in ("cool_on", "cool_off"):
        raise HTTPException(status_code=400, detail="invalid command")
    with Session(engine) as s:
        s.execute(text("""
            INSERT INTO commands(device_id, command) VALUES (:id, :cmd)
            ON CONFLICT (device_id) DO UPDATE SET command = EXCLUDED.command
        """), {"id": device_id, "cmd": body.command})
        s.commit()
    return {"ok": True, "device_id": device_id, "command": body.command}
