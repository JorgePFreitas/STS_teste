import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from livekit import api
from pydantic import BaseModel

load_dotenv(".env.local")
load_dotenv()

BASE_DIR = Path(__file__).parent
AGENT_NAME = "cobranca"


class TokenRequest(BaseModel):
    room_name: str | None = None
    participant_identity: str | None = None
    participant_name: str | None = None


app = FastAPI(title="Teste de Cobrança por Voz")


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True}


@app.post("/api/token")
async def token(request: TokenRequest) -> dict:
    room_name = request.room_name or f"cobranca-{secrets.token_hex(4)}"
    identity = request.participant_identity or f"user-{secrets.token_hex(4)}"

    jwt = (
        api.AccessToken(
            os.getenv("LIVEKIT_API_KEY", "devkey"),
            os.getenv("LIVEKIT_API_SECRET", "secret"),
        )
        .with_identity(identity)
        .with_name(request.participant_name or "Cliente")
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            ),
        )
        .with_room_config(
            api.RoomConfiguration(
                agents=[api.RoomAgentDispatch(agent_name=AGENT_NAME)],
            ),
        )
        .to_jwt()
    )

    return {
        "server_url": os.getenv("LIVEKIT_URL", "ws://localhost:7880"),
        "participant_token": jwt,
    }


app.mount("/", StaticFiles(directory=str(BASE_DIR / "static"), html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
