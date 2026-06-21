"""REST API — WebSocket for dashboard real-time updates."""

from __future__ import annotations

from contextlib import suppress
from typing import Any

from fastapi import APIRouter, WebSocket

router = APIRouter(prefix="/ws", tags=["websocket"])

_active_connections: list[WebSocket] = []


@router.websocket("/events")
async def websocket_events(websocket: WebSocket) -> None:
    await websocket.accept()
    _active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        _active_connections.remove(websocket)


async def broadcast_event(event: str, data: dict[str, Any]) -> None:
    """Broadcast an event to all connected dashboard clients."""
    for ws in _active_connections:
        with suppress(Exception):
            await ws.send_json({"event": event, "data": data})
