"""
Industrial Electrical RCA FastAPI Server.
Provides:
• GET  /api/scenarios - List pre-configured industrial incident scenarios (1-click triggerable)
• POST /api/analyze   - 1-Click trigger running all 5 coordinating agents, returning live telemetry, SOE, and RCA report
• GET  /api/topology  - Returns live Single-Line Diagram (SLD) power flow graph
• POST /alerts        - Ingests SCADA / Protection Relay alert payloads (AlertManager / IEC 61850)
• WS   /process/{id}  - WebSocket stream emitting real-time multi-agent reasoning
"""

import uuid
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, status, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from electrical_models import ElectricalAlertGroup, ElectricalAlert, SLDTopologyResponse
from electrical_rca_manager import ElectricalRCAManager
from electrical_agents import query_sld_topology_fn

app = FastAPI(
    title="Industrial Electrical Single-Line Diagram (SLD) Root Cause Analysis API",
    description="Multi-agent RCA pipeline: Grid Incomer -> 11kV VCB -> Step-down Transformer -> LT MCC -> VFD Motor",
    version="2.1.0"
)

# Enable CORS for all frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for WebSocket sessions
alert_store: Dict[str, ElectricalAlertGroup] = {}

# Pre-packaged Realistic Industrial Electrical Scenarios
PREDEFINED_SCENARIOS = {
    "motor_ground_fault": {
        "id": "motor_ground_fault",
        "title": "Motor Phase R Stator Earth Fault (50N)",
        "subtitle": "250 kW Boiler Feed Water Pump (MTR-VFD-01)",
        "asset_tag": "MTR-VFD-01",
        "severity": "CRITICAL",
        "fault_type": "Insulation Breakdown",
        "voltage": "415V",
        "trip_current": "1,240.5 A",
        "pickup": "50.0 A",
        "clearing_time": "65 ms",
        "ansi_codes": ["50N (Inst Earth Fault)", "49D (VFD Overcurrent)", "94 (Trip Coil)"],
        "description": "Severe insulation flashover on Phase R stator winding to earthed frame. Downstream breaker FD-MTR-01 trips in 65ms, successfully isolating fault before upstream 11kV VCB trips.",
        "payload": {
            "version": "4",
            "groupKey": "{}:{alertname=\"MotorPhaseREarthFaultInstantaneousTrip\"}",
            "status": "firing",
            "receiver": "electrical-scada-webhook",
            "groupLabels": {
                "alertname": "MotorPhaseREarthFaultInstantaneousTrip",
                "severity": "critical",
                "substation": "Substation-01",
                "voltage_level": "415V"
            },
            "commonLabels": {
                "alertname": "MotorPhaseREarthFaultInstantaneousTrip",
                "severity": "critical",
                "substation": "Substation-01",
                "asset_tag": "MTR-VFD-01",
                "service": "MTR-VFD-01",
                "voltage_level": "415V",
                "relay_tag": "RELAY-MTR-01",
                "breaker_feeder": "FD-MTR-01",
                "drive_type": "ABB ACS880 VFD 250kW"
            },
            "commonAnnotations": {
                "summary": "Phase R Instantaneous Ground Fault (ANSI 50N) Tripped on 250kW Boiler Feed Pump",
                "description": "Peak fault current of 1240.5 A detected on Phase R. Feeder breaker FD-MTR-01 tripped via trip coil 94. Upstream MCC-01 and 11kV VCB healthy.",
                "trip_current_amps": "1240.5",
                "relay_pickup_amps": "50.0",
                "clearing_time_ms": "65"
            },
            "externalURL": "http://scada-historian:8080/waveforms/event-20261020-001",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": "MotorPhaseREarthFaultInstantaneousTrip",
                        "severity": "critical",
                        "substation": "Substation-01",
                        "asset_tag": "MTR-VFD-01",
                        "voltage_level": "415V"
                    },
                    "annotations": {
                        "summary": "Phase R Instantaneous Ground Fault (ANSI 50N)",
                        "description": "Peak current 1240.5 A on Phase R. Feeder breaker FD-MTR-01 tripped."
                    },
                    "startsAt": "2026-10-20T11:20:00Z"
                }
            ]
        }
    },
    "transformer_overtemp": {
        "id": "transformer_overtemp",
        "title": "Transformer Winding Overtemp (49T) & Buchholz (63)",
        "subtitle": "2.5 MVA Distribution Transformer (TR-11KV-415V-01)",
        "asset_tag": "TR-11KV-415V-01",
        "severity": "HIGH",
        "fault_type": "Thermal & Gas Alarm",
        "voltage": "11kV / 415V",
        "trip_current": "3,480 A Secondary",
        "pickup": "115°C WTI Trip",
        "clearing_time": "120 s (Stage 1 Alarm)",
        "ansi_codes": ["49T (Winding Temp Alarm)", "63 (Buchholz Gas Relay)", "49OT (Oil Temp)"],
        "description": "Harmonic loading from 6-pulse VFD drives generated severe core heating. Winding temp reaches 118°C and Buchholz gas chamber accumulates 240ml of combustible gas.",
        "payload": {
            "version": "4",
            "groupKey": "{}:{alertname=\"TransformerWindingOvertempAndBuchholzAlarm\"}",
            "status": "firing",
            "receiver": "electrical-scada-webhook",
            "groupLabels": {
                "alertname": "TransformerWindingOvertempAndBuchholzAlarm",
                "severity": "warning",
                "substation": "Substation-01",
                "voltage_level": "11kV/415V"
            },
            "commonLabels": {
                "alertname": "TransformerWindingOvertempAndBuchholzAlarm",
                "severity": "warning",
                "substation": "Substation-01",
                "asset_tag": "TR-11KV-415V-01",
                "service": "TR-11KV-415V-01",
                "voltage_level": "11kV/415V",
                "relay_tag": "RELAY-TR-01"
            },
            "commonAnnotations": {
                "summary": "Transformer TR-1 Winding Temp 118°C and Buchholz Gas Relay 240ml Alarm",
                "description": "Thermal overload condition detected on 2.5 MVA Transformer TR-1. Buchholz float tilt sensor initiated SCADA alarm."
            },
            "externalURL": "http://scada-historian:8080/events?device=TR-11KV-415V-01",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": "TransformerWindingOvertempAndBuchholzAlarm",
                        "severity": "warning",
                        "substation": "Substation-01",
                        "asset_tag": "TR-11KV-415V-01"
                    },
                    "annotations": {
                        "summary": "Transformer Winding High Temperature Stage 1",
                        "description": "WTI sensor: 118°C. Buchholz gas volume: 240ml."
                    },
                    "startsAt": "2026-10-20T11:22:00Z"
                }
            ]
        }
    },
    "grid_voltage_sag": {
        "id": "grid_voltage_sag",
        "title": "11kV Grid Voltage Sag (27) & VFD Bus Undervoltage",
        "subtitle": "Grid Incomer (GRID-INC-01) → Motor (MTR-VFD-01)",
        "asset_tag": "GRID-INC-01",
        "severity": "CRITICAL",
        "fault_type": "Power Quality Sag",
        "voltage": "11kV",
        "trip_current": "Nominal",
        "pickup": "0.80 Un (27 Undervolt)",
        "clearing_time": "180 ms Sag Duration",
        "ansi_codes": ["27 (Undervoltage)", "47 (Phase Sequence Unbalance)", "81 (Frequency Deviation)"],
        "description": "External utility 33kV line flashover causes an 11kV voltage dip to 72% for 180ms. The VFD DC bus drops to 320V DC, causing a consequential process motor trip while main breakers remain closed.",
        "payload": {
            "version": "4",
            "groupKey": "{}:{alertname=\"GridVoltageDipAndCascadeVFDStop\"}",
            "status": "firing",
            "receiver": "electrical-scada-webhook",
            "groupLabels": {
                "alertname": "GridVoltageDipAndCascadeVFDStop",
                "severity": "critical",
                "substation": "Substation-01",
                "voltage_level": "11kV"
            },
            "commonLabels": {
                "alertname": "GridVoltageDipAndCascadeVFDStop",
                "severity": "critical",
                "substation": "Substation-01",
                "asset_tag": "GRID-INC-01",
                "service": "GRID-INC-01",
                "voltage_level": "11kV",
                "relay_tag": "RELAY-GRID-01"
            },
            "commonAnnotations": {
                "summary": "Grid Incomer 11kV Sag to 7.92 kV (72% Nominal) Triggered VFD DC Bus Undervoltage",
                "description": "180ms transient voltage sag on utility grid incomer caused DC bus collapse on downstream VFD motor drives."
            },
            "externalURL": "http://scada-historian:8080/events?device=GRID-INC-01",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": "GridVoltageDipAndCascadeVFDStop",
                        "severity": "critical",
                        "substation": "Substation-01",
                        "asset_tag": "GRID-INC-01"
                    },
                    "annotations": {
                        "summary": "Grid Voltage Sag 27 Triggered",
                        "description": "Voltage dip to 72% nominal."
                    },
                    "startsAt": "2026-10-20T11:24:00Z"
                }
            ]
        }
    }
}

class AnalyzeRequest(BaseModel):
    scenario_id: Optional[str] = "motor_ground_fault"
    custom_payload: Optional[ElectricalAlertGroup] = None

@app.get("/")
def health_check():
    return {
        "status": "online",
        "system": "Industrial Electrical Agentic RCA Platform",
        "version": "2.1.0",
        "author": "Amaresh Das",
        "topology": "Grid Incomer (33kV/11kV) -> 11kV VCB -> Step-down Transformer (2.5 MVA Dyn11) -> LT MCC (415V) -> VFD Motor (250kW)"
    }

@app.get("/api/scenarios")
def get_scenarios():
    """Returns all pre-packaged 1-click testable industrial electrical incident scenarios."""
    return list(PREDEFINED_SCENARIOS.values())

@app.get("/api/topology")
@app.get("/topology")
def get_topology():
    """Returns the Single-Line Diagram power distribution topology."""
    return query_sld_topology_fn(["GRID-INC-01", "VCB-11KV-01", "TR-11KV-415V-01", "MCC-415V-01", "MTR-VFD-01"])

@app.post("/api/analyze")
async def analyze_incident(req: AnalyzeRequest):
    """
    1-Click Analysis Endpoint:
    Triggers all 5 coordinating agents (SLDGraphAgent, RelayTelemetryAgent,
    SOEHistorianAgent, EquipmentSpecAgent, ElectricalRCASummaryAgent)
    and returns comprehensive structured findings and generated RCA report.
    """
    try:
        # Determine payload
        if req.custom_payload:
            payload = req.custom_payload
        elif req.scenario_id and req.scenario_id in PREDEFINED_SCENARIOS:
            scenario_data = PREDEFINED_SCENARIOS[req.scenario_id]
            payload = ElectricalAlertGroup(**scenario_data["payload"])
        else:
            scenario_data = PREDEFINED_SCENARIOS["motor_ground_fault"]
            payload = ElectricalAlertGroup(**scenario_data["payload"])

        manager = ElectricalRCAManager()
        result = await manager.run_with_details(payload)
        return result
    except Exception as e:
        print(f"[API] Error in /api/analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alerts", status_code=status.HTTP_202_ACCEPTED)
async def receive_alerts(payload: ElectricalAlertGroup) -> dict[str, Any]:
    """
    Ingest a SCADA / Protection Relay alert payload and return a WebSocket session ID.
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
