from enum import Enum

class AgentName(str, Enum):
    """Names of agents in the Industrial Electrical RCA system."""
    SLD_GRAPH = "SLDGraphAgent"
    TELEMETRY = "RelayTelemetryAgent"
    SOE_HISTORIAN = "SOEHistorianAgent"
    EQUIPMENT_SPEC = "EquipmentSpecAgent"
    REPORT = "ElectricalRCASummaryAgent"

class AgentType(str, Enum):
    """Types of agents in the Industrial Electrical RCA system."""
    SLD_GRAPH = "sld_graph"
    TELEMETRY = "telemetry"
    SOE_HISTORIAN = "soe_historian"
    EQUIPMENT_SPEC = "equipment_spec"
    REPORT = "rca_summary"

# Mapping from agent names to their types
AGENT_TYPE_MAP = {
    AgentName.SLD_GRAPH: AgentType.SLD_GRAPH,
    AgentName.TELEMETRY: AgentType.TELEMETRY,
    AgentName.SOE_HISTORIAN: AgentType.SOE_HISTORIAN,
    AgentName.EQUIPMENT_SPEC: AgentType.EQUIPMENT_SPEC,
    AgentName.REPORT: AgentType.REPORT
}