"""
Test script for Industrial Electrical RCA Pipeline.
Simulates a SCADA / IED alert payload on the Single-Line Diagram (SLD) topology:
Grid Incomer -> 11kV VCB -> Step-down Transformer -> LT MCC -> VFD Motor
"""

import sys
import os
import json
import asyncio
from datetime import datetime

# Add agents directory to sys.path
agents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents"))
if agents_dir not in sys.path:
    sys.path.insert(0, agents_dir)

from electrical_models import ElectricalAlertGroup, ElectricalAlert
from electrical_rca_manager import ElectricalRCAManager

# Industrial Electrical Alert Payload (SCADA / Protection Relay Alert)
ELECTRICAL_ALERT_PAYLOAD = {
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
        "description": "Peak fault current of 1240.5 A detected on Phase R. Feeder breaker FD-MTR-01 tripped via trip coil 94. Upstream MCC-01 healthy.",
        "trip_current_amps": "1240.5",
        "relay_pickup_amps": "50.0",
        "clearing_time_ms": "65"
    },
    "externalURL": "http://scada-historian.industrial:8080/events?device=MTR-VFD-01",
    "alerts": [
        {
            "status": "firing",
            "labels": {
                "alertname": "MotorPhaseREarthFaultInstantaneousTrip",
                "severity": "critical",
                "substation": "Substation-01",
                "asset_tag": "MTR-VFD-01",
                "voltage_level": "415V",
                "relay_tag": "RELAY-MTR-01"
            },
            "annotations": {
                "summary": "Phase R Instantaneous Ground Fault (ANSI 50N) Tripped on 250kW Boiler Feed Pump",
                "description": "Peak fault current of 1240.5 A detected on Phase R. Feeder breaker FD-MTR-01 tripped via trip coil 94."
            },
            "startsAt": datetime.utcnow().isoformat() + "Z",
            "generatorURL": "http://scada-historian.industrial:8080/waveforms/event-20261020-001"
        }
    ]
}

async def main():
    # Reconfigure stdout for UTF-8 on Windows
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 80)
    print("[ELECTRICAL RCA] INDUSTRIAL ELECTRICAL SINGLE-LINE DIAGRAM (SLD) ROOT CAUSE ANALYSIS")
    print("=" * 80)
    print("Topology: Grid Incomer -> 11kV VCB -> Step-down Transformer -> LT MCC -> VFD Motor")
    print(f"Triggering Alert: {ELECTRICAL_ALERT_PAYLOAD['commonLabels']['alertname']}")
    print(f"Asset: {ELECTRICAL_ALERT_PAYLOAD['commonLabels']['asset_tag']} | Substation: {ELECTRICAL_ALERT_PAYLOAD['commonLabels']['substation']}")
    print("-" * 80)

    # Ingest Alert
    alert_group = ElectricalAlertGroup(**ELECTRICAL_ALERT_PAYLOAD)

    # Run Multi-Agent RCA Manager
    manager = ElectricalRCAManager()
    report = await manager.run(alert_group)

    print("\n" + "=" * 80)
    print("GENERATED ELECTRICAL ROOT CAUSE ANALYSIS (RCA) REPORT:")
    print("=" * 80 + "\n")
    print(report)

    # Save output report to artifacts/results
    output_path = os.path.join(os.path.dirname(__file__), "sample_electrical_rca_report.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n✅ Report written to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
