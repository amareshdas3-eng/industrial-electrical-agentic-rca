from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Optional, Any

### Industrial Electrical Alert Models (Compatible with SCADA / AlertManager) ###

class ElectricalAlert(BaseModel):
    status: str = Field(..., description="Alert status: 'firing' or 'resolved'")
    labels: Dict[str, str] = Field(..., description="Labels: alertname, asset_tag, voltage_level, severity, substation, relay_tag")
    annotations: Dict[str, str] = Field(..., description="Annotations: summary, description, trip_value, pickup_setting")
    startsAt: datetime
    endsAt: Optional[datetime] = None
    generatorURL: Optional[str] = None

class ElectricalAlertGroup(BaseModel):
    version: str = Field(default="4", pattern=r"^\d+$")
    groupKey: str
    status: str
    receiver: str = "electrical-scada-webhook"
    groupLabels: Dict[str, str]
    commonLabels: Dict[str, str]
    commonAnnotations: Dict[str, str]
    externalURL: Optional[str] = "http://scada-historian:8080"
    alerts: List[ElectricalAlert]


### Single-Line Diagram (SLD) Topology Models ###

class ProtectionRelayMetadata(BaseModel):
    """Protection relay settings and ANSI device codes associated with switchgear."""
    relay_tag: str = Field(..., description="e.g. RELAY-VCB-01, RELAY-MCC-INCOMER")
    relay_type: str = Field(..., description="e.g. Numerical Feeder Protection, Differential, Motor Protection")
    ansi_codes: List[str] = Field(..., description="Configured ANSI protection functions: 50, 51, 50N, 51N, 87, 49, 27, 59, 63")
    pickup_current: Optional[str] = None
    time_multiplier_tms: Optional[float] = None
    last_trip_flag: Optional[str] = None

class ElectricalAssetNode(BaseModel):
    """Node representing an electrical apparatus on the Single-Line Diagram."""
    asset_tag: str = Field(..., description="Unique tag: GRID-INC-01, VCB-11KV-01, TR-11KV-415V-01, MCC-415V-01, MTR-VFD-01")
    name: str = Field(..., description="Human readable name e.g. '11kV Vacuum Circuit Breaker'")
    asset_type: str = Field(..., description="'UtilityIncomer', 'VCB', 'Transformer', 'MCC', 'VFD_Motor'")
    voltage_level: str = Field(..., description="'33kV', '11kV', '415V'")
    rated_capacity: str = Field(..., description="e.g. '2500 kVA', '1250 A', '250 kW'")
    operating_status: str = Field(default="ENERGIZED", description="'ENERGIZED', 'DE_ENERGIZED', 'TRIPPED', 'OPEN', 'FAULT'")
    protection: Optional[ProtectionRelayMetadata] = None
    location: Optional[str] = "Substation-01"
    attributes: Optional[Dict[str, Any]] = None

class ElectricalFeederEdge(BaseModel):
    """Relationship representing electrical power connection / cable run between assets."""
    source_tag: str
    target_tag: str
    cable_spec: str = Field(..., description="e.g. '3C x 185 sq.mm XLPE AL Cable', '3200A Sandwich Busduct'")
    rated_voltage: str = Field(..., description="'11kV', '415V'")
    running_status: str = Field(default="CLOSED", description="'CLOSED', 'OPEN', 'ISOLATED'")
    breaker_status: Optional[str] = "CLOSED"

class SLDTopologyGraph(BaseModel):
    """
    SLD Topology context for an impacted electrical asset:
    - current: the focal asset where the alert/trip originated
    - upstream: power sources and upstream switchgear energizing 'current'
    - downstream: loads and downstream panels fed by 'current'
    """
    current: ElectricalAssetNode
    upstream: List[ElectricalAssetNode]
    downstream: List[ElectricalAssetNode]

class SLDTopologyResponse(BaseModel):
    assets: List[SLDTopologyGraph]

class SLDDependencies(BaseModel):
    upstream_tags: List[str] = Field(..., description="List of upstream asset tags feeding this asset")
    downstream_tags: List[str] = Field(..., description="List of downstream asset tags fed by this asset")


### Telemetry and Sequence of Events (SOE) Models ###

class ElectricalTelemetry(BaseModel):
    asset_tag: str
    timestamp: datetime
    phase_current_ir: float = Field(..., description="Phase R Current in Amperes")
    phase_current_iy: float = Field(..., description="Phase Y Current in Amperes")
    phase_current_ib: float = Field(..., description="Phase B Current in Amperes")
    voltage_vry: float = Field(..., description="Line-to-Line Voltage V_RY in Volts")
    voltage_vyb: float = Field(..., description="Line-to-Line Voltage V_YB in Volts")
    voltage_vbr: float = Field(..., description="Line-to-Line Voltage V_BR in Volts")
    frequency_hz: float = Field(default=50.0, description="System frequency in Hz")
    power_factor: float = Field(default=0.88, description="Power factor")
    active_power_kw: float
    thd_voltage_percent: float = Field(default=1.8, description="Total Harmonic Distortion V_THD %")
    active_relay_flags: List[str] = Field(default_factory=list, description="Active ANSI protection trip flags")

class SOELogRecord(BaseModel):
    timestamp_iso: str = Field(..., description="High precision ISO timestamp with milliseconds")
    device_tag: str
    event_type: str = Field(..., description="'ALARM', 'TRIP_COMMAND', 'BREAKER_OPEN', 'UNDERVOLTAGE_PICKUP', 'OVERCURRENT_PICKUP'")
    severity: str
    description: str
    raw_measurements: Optional[Dict[str, Any]] = None

class AssetEngineeringSpec(BaseModel):
    asset_tag: str
    manufacturer: str
    model_number: str
    commissioning_date: str
    impedance_percent: Optional[float] = None
    thermal_withstand_limit: Optional[str] = None
    tcc_curve_type: Optional[str] = None
    last_megger_insulation_mohm: Optional[float] = None
    last_dga_status: Optional[str] = None
    notes: Optional[str] = None
