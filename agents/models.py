"""
Industrial Electrical Data Models.
Exports all Single-Line Diagram (SLD) topology, protection relay, telemetry, and alert models.
"""

from electrical_models import (
    ElectricalAlert,
    ElectricalAlertGroup,
    ProtectionRelayMetadata,
    ElectricalAssetNode,
    ElectricalFeederEdge,
    SLDTopologyGraph,
    SLDTopologyResponse,
    SLDDependencies,
    ElectricalTelemetry,
    SOELogRecord,
    AssetEngineeringSpec,
    # Backward compatibility aliases for standard webhook ingestion
    ElectricalAlert as Alert,
    ElectricalAlertGroup as AlertGroup
)

__all__ = [
    "ElectricalAlert",
    "ElectricalAlertGroup",
    "ProtectionRelayMetadata",
    "ElectricalAssetNode",
    "ElectricalFeederEdge",
    "SLDTopologyGraph",
    "SLDTopologyResponse",
    "SLDDependencies",
    "ElectricalTelemetry",
    "SOELogRecord",
    "AssetEngineeringSpec",
    "Alert",
    "AlertGroup"
]