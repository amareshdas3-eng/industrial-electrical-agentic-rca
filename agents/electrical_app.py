"""
Industrial Electrical RCA FastAPI Server.
Provides:
• POST /alerts        - Ingests SCADA / Protection Relay alert payloads (AlertGroup / ElectricalAlertGroup)
• GET  /topology      - Returns live Single-Line Diagram (SLD) topology graph
• WS   /process/{id}  - WebSocket stream emitting real-time multi-agent reasoning, IED telemetry, SOE logs, and Markdown RCA report.
"""

import uuid
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, status, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from electrical_models import ElectricalAlertGroup, SLDTopologyResponse
from electrical_rca_manager import ElectricalRCAManager
from electrical_agents import query_sld_topology_fn

app = FastAPI(
    title="Industrial Electrical Single-Line Diagram (SLD) Root Cause Analysis API",
    description="Multi-agent RCA pipeline: Grid Incomer -> 11kV VCB -> Step-down Transformer -> LT MCC -> VFD Motor",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store alerts temporarily by websocket ID
alert_store: Dict[str, ElectricalAlertGroup] = {}

@app.get("/")
def health_check():
    return {
        "status": "online",
        "system": "Industrial Electrical Agentic RCA",
        "topology": "Grid Incomer -> 11kV VCB -> Step-down Transformer -> LT MCC -> VFD Motor"
    }

@app.get("/topology")
def get_topology():
    """Returns the Single-Line Diagram power distribution topology."""
    return query_sld_topology_fn(["GRID-INC-01", "VCB-11KV-01", "TR-11KV-415V-01", "MCC-415V-01", "MTR-VFD-01"])

@app.post("/alerts", status_code=status.HTTP_202_ACCEPTED)
async def receive_alerts(payload: ElectricalAlertGroup) -> dict[str, Any]:
    """
    Receive an electrical incident alert and return a unique websocket processing ID.
    """
    try:
        count = len(payload.alerts)
        asset_tag = payload.commonLabels.get("asset_tag", "Unknown")
        print(f" Received {count} electrical alert(s) on asset: {asset_tag} | status={payload.status}")
        
        ws_id = str(uuid.uuid4())
        alert_store[ws_id] = payload
        return {"websocket_id": ws_id, "asset_tag": asset_tag}
    except Exception as exc:
        print(f" Failed to ingest electrical alert: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

@app.websocket("/process/{ws_id}")
async def process_alerts(websocket: WebSocket, ws_id: str):
    """
    Connect to stream real-time multi-agent electrical RCA findings and final Markdown report.
    """
    try:
        await websocket.accept()
        
        if ws_id not in alert_store:
            await websocket.send_json({
                "type": "error",
                "agent": "system",
                "data": "Websocket session ID not found or already consumed."
            })
            await websocket.close()
            return
        
        payload = alert_store[ws_id]
        manager = ElectricalRCAManager(websocket=websocket)
        report = await manager.run(payload)
        
        # Cleanup
        if ws_id in alert_store:
            del alert_store[ws_id]
            
        await websocket.close()
    except WebSocketDisconnect:
        print(f"[WebSocket] Client disconnected from session {ws_id}")
    except Exception as exc:
        print(f"[WebSocket] Error during RCA processing: {exc}")
        try:
            await websocket.send_json({
                "type": "error",
                "agent": "system",
                "data": str(exc)
            })
        except:
            pass
        finally:
            await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("electrical_app:app", host="0.0.0.0", port=8001, reload=True)
