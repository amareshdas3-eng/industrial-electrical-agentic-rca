"""
Multi-Agent System for Industrial Electrical Single-Line Diagram (SLD) Root Cause Analysis.
Industrial electrical power distribution topology:
Grid Incomer -> 11kV VCB -> Step-down Transformer -> LT MCC -> VFD Motor
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

from agents import Agent, ModelSettings, function_tool, AgentOutputSchema
from electrical_models import (
    ElectricalAssetNode,
    ProtectionRelayMetadata,
    SLDTopologyGraph,
    SLDTopologyResponse,
    SLDDependencies,
    ElectricalTelemetry,
    SOELogRecord,
    AssetEngineeringSpec
)

# ---------------------------------------------------------------------------
# 1. SLD GRAPH CLIENT (Neo4j with In-Memory Cache Fallback)
# ---------------------------------------------------------------------------

class SLDGraphClient:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self._cache_file = os.path.join(os.path.dirname(__file__), "..", "scripts", "sld_graph_cache.json")
        self._in_memory_db = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        if os.path.exists(self._cache_file):
            try:
                with open(self._cache_file, "r") as f:
                    data = json.load(f)
                    return data.get("nodes", {})
            except Exception as e:
                print(f"Warning: Could not read cache file {self._cache_file}: {e}")
        # Default built-in SLD topology
        return {
            "GRID-INC-01": {
                "asset_tag": "GRID-INC-01",
                "name": "33kV/11kV Utility Grid Incomer",
                "asset_type": "UtilityIncomer",
                "voltage_level": "11kV",
                "rated_capacity": "40 MVA Fault Level",
                "operating_status": "ENERGIZED",
                "location": "Outdoor Switchyard",
                "protection": {
                    "relay_tag": "RELAY-GRID-01",
                    "relay_type": "Siemens 7SJ82 Feeder Protection",
                    "ansi_codes": ["50", "51", "50N", "51N", "27", "59", "81"],
                    "pickup_current": "1200A",
                    "time_multiplier_tms": 0.25,
                    "last_trip_flag": "NORMAL"
                },
                "upstream": [],
                "downstream": ["VCB-11KV-01"]
            },
            "VCB-11KV-01": {
                "asset_tag": "VCB-11KV-01",
                "name": "11kV Vacuum Circuit Breaker (Feeder 1)",
                "asset_type": "VCB",
                "voltage_level": "11kV",
                "rated_capacity": "1250 A / 25 kA Breaking",
                "operating_status": "ENERGIZED",
                "location": "11kV Indoor Switchgear Room",
                "protection": {
                    "relay_tag": "RELAY-VCB-01",
                    "relay_type": "ABB REF615 Numerical Feeder Protection",
                    "ansi_codes": ["50", "51", "50N", "51N"],
                    "pickup_current": "1250A (1.0x In)",
                    "time_multiplier_tms": 0.15,
                    "last_trip_flag": "NORMAL"
                },
                "upstream": ["GRID-INC-01"],
                "downstream": ["TR-11KV-415V-01"]
            },
            "TR-11KV-415V-01": {
                "asset_tag": "TR-11KV-415V-01",
                "name": "Step-down Distribution Transformer (TR-1)",
                "asset_type": "Transformer",
                "voltage_level": "11kV/415V",
                "rated_capacity": "2500 kVA (2.5 MVA)",
                "operating_status": "ENERGIZED",
                "location": "Transformer Yard Bay 1",
                "attributes": {
                    "vector_group": "Dyn11",
                    "impedance_percent": 6.25,
                    "cooling": "ONAN"
                },
                "protection": {
                    "relay_tag": "RELAY-TR-01",
                    "relay_type": "Transformer Protection Unit",
                    "ansi_codes": ["49T", "49OT", "63", "87T", "51N"],
                    "last_trip_flag": "NORMAL"
                },
                "upstream": ["VCB-11KV-01"],
                "downstream": ["MCC-415V-01"]
            },
            "MCC-415V-01": {
                "asset_tag": "MCC-415V-01",
                "name": "415V Low Tension Motor Control Center (MCC-1)",
                "asset_type": "MCC",
                "voltage_level": "415V",
                "rated_capacity": "3200 A Busbar / 50 kA Fault Withstand",
                "operating_status": "ENERGIZED",
                "location": "LT Switchgear Room",
                "attributes": {
                    "incomer_device": "ACB 3200A 4-Pole Drawout",
                    "busbar_rating": "3200A Copper"
                },
                "protection": {
                    "relay_tag": "RELAY-MCC-INCOMER",
                    "relay_type": "Microprocessor Trip Unit (LSIG)",
                    "ansi_codes": ["50", "51", "51N", "27"],
                    "pickup_current": "3000A",
                    "time_multiplier_tms": 0.10,
                    "last_trip_flag": "NORMAL"
                },
                "upstream": ["TR-11KV-415V-01"],
                "downstream": ["MTR-VFD-01"]
            },
            "MTR-VFD-01": {
                "asset_tag": "MTR-VFD-01",
                "name": "Boiler Feed Water Pump VFD Motor",
                "asset_type": "VFD_Motor",
                "voltage_level": "415V",
                "rated_capacity": "250 kW / 410 A FLC",
                "operating_status": "ENERGIZED",
                "location": "Boiler House Floor 1",
                "attributes": {
                    "drive_model": "ABB ACS880 250kW 6-Pulse IGBT",
                    "motor_type": "3-Phase Squirrel Cage Induction Motor",
                    "feeder_breaker": "MCCB 630A Thermal-Magnetic"
                },
                "protection": {
                    "relay_tag": "RELAY-MTR-01",
                    "relay_type": "Integrated VFD Protection + REM615",
                    "ansi_codes": ["49", "50", "50N", "51LR", "27", "38"],
                    "pickup_current": "450A",
                    "last_trip_flag": "NORMAL"
                },
                "upstream": ["MCC-415V-01"],
                "downstream": []
            }
        }

    def get_node_metadata(self, asset_tag: str) -> ElectricalAssetNode:
        # Check in-memory store
        tag = asset_tag.strip().upper()
        # Handle aliases or service names
        alias_map = {
            "GRID": "GRID-INC-01",
            "GRID-INCOMER": "GRID-INC-01",
            "VCB": "VCB-11KV-01",
            "11KV-VCB": "VCB-11KV-01",
            "TRANSFORMER": "TR-11KV-415V-01",
            "STEP-DOWN TRANSFORMER": "TR-11KV-415V-01",
            "MCC": "MCC-415V-01",
            "LT-MCC": "MCC-415V-01",
            "VFD": "MTR-VFD-01",
            "MOTOR": "MTR-VFD-01",
            "VFD-MOTOR": "MTR-VFD-01"
        }
        resolved_tag = alias_map.get(tag, tag)
        
        # Try Neo4j first
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            with driver.session() as session:
                res = session.run("""
                    MATCH (n:ElectricalAsset)
                    WHERE n.asset_tag = $tag OR n.name CONTAINS $tag
                    RETURN n
                """, tag=resolved_tag).single()
                if res:
                    props = dict(res["n"])
                    prot = None
                    if "relay_tag" in props:
                        prot = ProtectionRelayMetadata(
                            relay_tag=props.get("relay_tag", "UNKNOWN"),
                            relay_type=props.get("relay_type", "Feeder Protection"),
                            ansi_codes=props.get("ansi_codes", "").split(","),
                            pickup_current=props.get("pickup_current"),
                            last_trip_flag=props.get("last_trip_flag")
                        )
                    return ElectricalAssetNode(
                        asset_tag=props["asset_tag"],
                        name=props["name"],
                        asset_type=props["asset_type"],
                        voltage_level=props["voltage_level"],
                        rated_capacity=props["rated_capacity"],
                        operating_status=props.get("operating_status", "ENERGIZED"),
                        location=props.get("location", "Substation"),
                        protection=prot
                    )
            driver.close()
        except Exception:
            pass # Fall back to in-memory

        if resolved_tag in self._in_memory_db:
            raw = self._in_memory_db[resolved_tag]
            prot = None
            if "protection" in raw:
                prot = ProtectionRelayMetadata(**raw["protection"])
            return ElectricalAssetNode(
                asset_tag=raw["asset_tag"],
                name=raw["name"],
                asset_type=raw["asset_type"],
                voltage_level=raw["voltage_level"],
                rated_capacity=raw["rated_capacity"],
                operating_status=raw.get("operating_status", "ENERGIZED"),
                location=raw.get("location", "Substation-01"),
                protection=prot,
                attributes=raw.get("attributes")
            )
        
        # Fallback default
        return ElectricalAssetNode(
            asset_tag=resolved_tag,
            name=f"Electrical Apparatus ({resolved_tag})",
            asset_type="Switchgear",
            voltage_level="415V",
            rated_capacity="Unknown"
        )

    def get_dependencies(self, asset_tag: str) -> SLDDependencies:
        tag = asset_tag.strip().upper()
        alias_map = {
            "GRID": "GRID-INC-01",
            "VCB": "VCB-11KV-01",
            "TRANSFORMER": "TR-11KV-415V-01",
            "MCC": "MCC-415V-01",
            "VFD": "MTR-VFD-01",
            "MOTOR": "MTR-VFD-01"
        }
        resolved_tag = alias_map.get(tag, tag)
        if resolved_tag in self._in_memory_db:
            raw = self._in_memory_db[resolved_tag]
            return SLDDependencies(
                upstream_tags=raw.get("upstream", []),
                downstream_tags=raw.get("downstream", [])
            )
        return SLDDependencies(upstream_tags=[], downstream_tags=[])

sld_client = SLDGraphClient()


# ---------------------------------------------------------------------------
# 2. AGENT TOOLS & FUNCTIONS
# ---------------------------------------------------------------------------

def query_sld_topology_fn(asset_tags: List[str]) -> SLDTopologyResponse:
    """
    Query the electrical Single-Line Diagram (SLD) topology for the given asset tags.
    Returns the focal apparatus, all upstream power sources (feeders/transformers/incomers),
    and all downstream connected equipment and branch loads.
    """
    print(f"[SLDGraphAgent] Querying Single-Line Diagram topology for: {asset_tags}")
    graphs = []
    for tag in asset_tags:
        current_node = sld_client.get_node_metadata(tag)
        deps = sld_client.get_dependencies(current_node.asset_tag)
        upstream_nodes = [sld_client.get_node_metadata(u) for u in deps.upstream_tags]
        downstream_nodes = [sld_client.get_node_metadata(d) for d in deps.downstream_tags]
        graphs.append(SLDTopologyGraph(
            current=current_node,
            upstream=upstream_nodes,
            downstream=downstream_nodes
        ))
    return SLDTopologyResponse(assets=graphs)


def get_electrical_telemetry_fn(asset_tag: str) -> str:
    """
    Fetch live switchgear IED telemetry for an electrical asset:
    3-phase currents (Ir, Iy, Ib), line voltages (Vry, Vyb, Vbr), frequency,
    power factor, active power kW, THD %, and active ANSI protection relay trip flags.
    """
    print(f"[TelemetryAgent] Polling IED telemetry for: {asset_tag}")
    tag = asset_tag.strip().upper()

    # Scenario telemetry based on asset
    if "MTR" in tag or "VFD" in tag:
        telemetry = {
            "asset_tag": "MTR-VFD-01",
            "timestamp": datetime.now().isoformat() + "Z",
            "current_ir_amps": 1240.5,
            "current_iy_amps": 412.0,
            "current_ib_amps": 398.2,
            "current_unbalance_percent": 68.4,
            "voltage_vry_volts": 348.0,
            "voltage_vyb_volts": 415.0,
            "voltage_vbr_volts": 352.0,
            "power_factor": 0.42,
            "thd_current_percent": 14.8,
            "drive_dc_bus_voltage": 320.0,  # Sagged below 540V DC normal
            "active_relay_flags": ["50N (Instantaneous Earth Fault)", "49D (Drive Thermal Overload)"],
            "breaker_aux_contact": "OPEN (Tripped via Protection Relay Trip Coil 94)"
        }
    elif "MCC" in tag:
        telemetry = {
            "asset_tag": "MCC-415V-01",
            "timestamp": datetime.now().isoformat() + "Z",
            "incomer_current_ir_amps": 1820.0,
            "incomer_current_iy_amps": 850.0,
            "incomer_current_ib_amps": 840.0,
            "busbar_voltage_vry_volts": 395.0,
            "busbar_voltage_vyb_volts": 414.0,
            "busbar_voltage_vbr_volts": 398.0,
            "power_factor": 0.81,
            "active_relay_flags": ["51N (IDMT Earth Fault Warning)"],
            "breaker_aux_contact": "CLOSED"
        }
    elif "TR" in tag:
        telemetry = {
            "asset_tag": "TR-11KV-415V-01",
            "timestamp": datetime.now().isoformat() + "Z",
            "primary_current_ir_amps": 68.2,
            "primary_current_iy_amps": 32.1,
            "primary_current_ib_amps": 31.8,
            "winding_temperature_r_degC": 94.5,
            "oil_temperature_degC": 78.2,
            "buchholz_gas_alarm": "CLEAR",
            "active_relay_flags": ["49T (Winding High Temperature Stage 1 Alarm)"],
            "breaker_aux_contact": "CLOSED"
        }
    elif "VCB" in tag:
        telemetry = {
            "asset_tag": "VCB-11KV-01",
            "timestamp": datetime.now().isoformat() + "Z",
            "feeder_current_ir_amps": 68.4,
            "feeder_current_iy_amps": 32.2,
            "feeder_current_ib_amps": 31.9,
            "bus_voltage_11kv": 10.82,
            "active_relay_flags": ["51N Pickup (Timer initiated)"],
            "breaker_aux_contact": "CLOSED"
        }
    else:
        telemetry = {
            "asset_tag": tag,
            "timestamp": datetime.now().isoformat() + "Z",
            "voltage": "Nominal",
            "current": "Balanced",
            "active_relay_flags": ["NORMAL"]
        }
    return json.dumps(telemetry, indent=2)


def get_soe_event_stream_fn(asset_tag: str, window_seconds: int = 60) -> str:
    """
    Query the Substation Sequence of Events (SOE) log recorder (1-millisecond resolution).
    Returns the exact high-precision chronological order of alarms, relay pickup events,
    trip coil energization, and auxiliary contact transitions.
    """
    print(f"[SOEHistorianAgent] Querying SOE millisecond recorder for: {asset_tag}")
    records = [
        {
            "timestamp_iso": "2026-10-20T11:20:00.000Z",
            "time_offset_ms": "T+000ms",
            "device": "MTR-VFD-01",
            "event_type": "MOTOR_STATOR_EARTH_FAULT",
            "severity": "CRITICAL",
            "description": "Insulation flashover detected on Motor Phase R winding to frame ground (Ir = 1240A spike)"
        },
        {
            "timestamp_iso": "2026-10-20T11:20:00.015Z",
            "time_offset_ms": "T+015ms",
            "device": "RELAY-MTR-01",
            "event_type": "PROTECTION_PICKUP",
            "severity": "HIGH",
            "description": "ANSI 50N (Instantaneous Earth Fault) pickup triggered at 1200A (> 50A threshold)"
        },
        {
            "timestamp_iso": "2026-10-20T11:20:00.035Z",
            "time_offset_ms": "T+035ms",
            "device": "RELAY-MTR-01",
            "event_type": "TRIP_COMMAND",
            "severity": "CRITICAL",
            "description": "Trip command issued to VFD Incomer MCCB trip coil (94)"
        },
        {
            "timestamp_iso": "2026-10-20T11:20:00.042Z",
            "time_offset_ms": "T+042ms",
            "device": "MTR-VFD-01",
            "event_type": "VFD_DRIVE_FAULT",
            "severity": "CRITICAL",
            "description": "Inverter DC Bus link protection tripped on desaturation / IGBT overcurrent protection"
        },
        {
            "timestamp_iso": "2026-10-20T11:20:00.065Z",
            "time_offset_ms": "T+065ms",
            "device": "FD-MTR-01",
            "event_type": "BREAKER_AUX_OPEN",
            "severity": "INFO",
            "description": "Feeder Breaker FD-MTR-01 auxiliary contact (52a) transitioned to OPEN, clearing fault from LT MCC"
        },
        {
            "timestamp_iso": "2026-10-20T11:20:00.080Z",
            "time_offset_ms": "T+080ms",
            "device": "MCC-415V-01",
            "event_type": "VOLTAGE_RECOVERY",
            "severity": "INFO",
            "description": "LT MCC Bus voltage restored to 415V nominal after fault clearance"
        },
        {
            "timestamp_iso": "2026-10-20T11:20:00.085Z",
            "time_offset_ms": "T+085ms",
            "device": "VCB-11KV-01",
            "event_type": "PROTECTION_RESET",
            "severity": "INFO",
            "description": "Upstream 11kV VCB relay REF615 51N backup timer reset (fault cleared downstream within coordination margin)"
        }
    ]
    return json.dumps(records, indent=2)


def get_equipment_spec_and_protection_coordination_fn(asset_tag: str) -> str:
    """
    Retrieve equipment design ratings, nameplate data, relay coordination Time-Current Characteristic (TCC)
    margins, and historical insulation/maintenance records (Megger test, DGA, thermal scan).
    """
    print(f"[EquipmentSpecAgent] Retrieving engineering specs & TCC curves for: {asset_tag}")
    tag = asset_tag.strip().upper()
    specs = {
        "MTR-VFD-01": {
            "nameplate": {
                "asset_tag": "MTR-VFD-01",
                "motor_manufacturer": "Siemens / ABB",
                "rated_kw": 250,
                "full_load_amps": 410,
                "voltage": 415,
                "power_factor": 0.88,
                "insulation_class": "Class F with Class B temperature rise (130C limit)",
                "bearing_type": "Insulated DE/NDE Bearings for VFD harmonic currents",
                "commissioning_date": "2021-04-15"
            },
            "protection_settings": {
                "50N_earth_fault_pickup": "50 A (Instantaneous, time delay: 0.03s)",
                "49_thermal_overload": "1.05x FLC (430A, cold curve t6x = 12s)",
                "51LR_locked_rotor": "3.5x FLC (1435A, delay: 4.0s)"
            },
            "maintenance_history": {
                "last_megger_insulation_resistance": "3.2 Mega-Ohms (CRITICAL DEGRADATION from 150 MΩ baseline)",
                "last_testing_date": "2026-08-10",
                "vibration_analysis": "Normal (overall RMS 1.8 mm/s)",
                "recommendation_flag": "Stator rewinding or insulation varnish dip recommended due to moisture ingress"
            }
        },
        "TR-11KV-415V-01": {
            "nameplate": {
                "asset_tag": "TR-11KV-415V-01",
                "mva_rating": 2.5,
                "voltage_ratio": "11000V / 415V",
                "vector_group": "Dyn11",
                "percent_impedance": 6.25,
                "bil_rating": "75 kV Peak (11kV side)"
            },
            "protection_settings": {
                "49T_winding_temp_alarm": "95 deg C",
                "49T_winding_temp_trip": "115 deg C",
                "63_buchholz_alarm": "Gas volume > 200 ml"
            },
            "maintenance_history": {
                "dga_status": "Condition 1 (Normal per IEEE C57.104)",
                "oil_bdv_breakdown_voltage": "62 kV (Good)"
            }
        },
        "VCB-11KV-01": {
            "nameplate": {
                "asset_tag": "VCB-11KV-01",
                "rated_voltage": "12 kV",
                "rated_current": "1250 A",
                "short_circuit_breaking": "25 kA rms / 3s"
            },
            "protection_settings": {
                "relay": "ABB REF615",
                "51_idmt_pickup": "1250 A (TMS = 0.15, IEC Standard Inverse)",
                "51N_idmt_earth_fault": "120 A (TMS = 0.15, time delay to clear downstream: 0.180s)"
            }
        }
    }
    matched = specs.get(tag, specs.get("MTR-VFD-01"))
    return json.dumps(matched, indent=2)

# Function tools for Agents
query_sld_topology = function_tool(query_sld_topology_fn)
get_electrical_telemetry = function_tool(get_electrical_telemetry_fn)
get_soe_event_stream = function_tool(get_soe_event_stream_fn)
get_equipment_spec_and_protection_coordination = function_tool(get_equipment_spec_and_protection_coordination_fn)


# ---------------------------------------------------------------------------
# 3. AGENT DEFINITIONS
# ---------------------------------------------------------------------------

SLD_GRAPH_PROMPT = (
    "You are an Industrial Electrical Single-Line Diagram (SLD) Topology Agent. "
    "Your objective is to analyze electrical power distribution graphs stored in Neo4j. "
    "The SLD topology represents power flow: "
    "Grid Incomer (33kV/11kV) -> 11kV VCB -> Step-down Transformer (11kV/415V Dyn11) -> LT MCC (415V) -> VFD Motor (250kW). "
    "Given an incoming alert on an electrical asset, use query_sld_topology to identify: "
    "1. The focal asset and its voltage level. "
    "2. Upstream power sources that feed this asset (breakers, transformers, incomers). "
    "3. Downstream connected switchboards and loads fed by this asset. "
    "Return the complete SLD topology graph response."
)

sld_graph_agent = Agent(
    name="SLDGraphAgent",
    instructions=SLD_GRAPH_PROMPT,
    tools=[query_sld_topology],
    output_type=AgentOutputSchema(SLDTopologyResponse, strict_json_schema=False),
    model_settings=ModelSettings(tool_choice="required")
)

TELEMETRY_PROMPT = (
    "You are an Electrical Switchgear Telemetry Agent. "
    "Your role is to inspect Intelligent Electronic Device (IED) metering and protection relay telemetry. "
    "For the affected electrical asset(s) and their upstream/downstream neighbors: "
    "1. Read the 3-phase currents (Ir, Iy, Ib) and check for phase unbalance or short-circuit magnitude. "
    "2. Read the Line-to-Line voltages and inspect for voltage sags or bus dips. "
    "3. Check the active ANSI protection trip flags (50, 51, 50N, 87, 49, 27, 59, 63). "
    "4. Determine whether the breaker contact is OPEN (tripped) or CLOSED."
)

telemetry_agent = Agent(
    name="RelayTelemetryAgent",
    instructions=TELEMETRY_PROMPT,
    tools=[get_electrical_telemetry],
    output_type=str,
    model_settings=ModelSettings(tool_choice="required")
)

SOE_PROMPT = (
    "You are an Electrical Sequence of Events (SOE) Historian Agent. "
    "Your responsibility is to analyze the high-resolution 1-millisecond timestamped event stream. "
    "Reconstruct the exact chronology of the incident: "
    "- What event occurred at T+0ms? (The initiating trigger) "
    "- Which protection relay picked up first? "
    "- Which breaker operated and at what millisecond? "
    "- Did protection coordination hold (downstream breaker cleared before upstream tripped), or was there a cascade trip?"
)

soe_historian_agent = Agent(
    name="SOEHistorianAgent",
    instructions=SOE_PROMPT,
    tools=[get_soe_event_stream],
    output_type=str,
    model_settings=ModelSettings(tool_choice="required")
)

SPEC_PROMPT = (
    "You are an Electrical Equipment Engineering & Protection Coordination Agent. "
    "Your duty is to correlate the fault with equipment design ratings, relay coordination (TCC) margins, "
    "and maintenance test logs (Megger insulation resistance, DGA dissolved gas analysis, thermal scan). "
    "Identify any degradation (e.g. low insulation resistance < 5 MΩ) or relay coordination discrepancies "
    "that explain why the electrical apparatus failed."
)

equipment_spec_agent = Agent(
    name="EquipmentSpecAgent",
    instructions=SPEC_PROMPT,
    tools=[get_equipment_spec_and_protection_coordination],
    output_type=str,
    model_settings=ModelSettings(tool_choice="required")
)

ELECTRICAL_RCA_PROMPT = (
    "You are a Senior Principal Electrical Power Systems Engineer and SRE Root Cause Analysis specialist. "
    "You produce rigorous, actionable IEEE/IEC-compliant Root Cause Analysis reports for industrial electrical incidents.\n\n"
    "You are given:\n"
    "1. The original SCADA / Protection Alert JSON.\n"
    "2. Single-Line Diagram (SLD) topology: Grid Incomer -> 11kV VCB -> Step-down Transformer -> LT MCC -> VFD Motor.\n"
    "3. IED telemetry (Phase currents, bus voltages, ANSI trip flags: 50, 51, 50N, 49, 27).\n"
    "4. Sequence of Events (SOE) millisecond-by-millisecond timeline.\n"
    "5. Equipment engineering specs, protection coordination curves, and maintenance history.\n\n"
    "Structure your response strictly in the following Markdown format:\n\n"
    "# Industrial Electrical Root Cause Analysis (RCA) Report\n\n"
    "## 1. Executive Incident Summary\n"
    "Concise description of the electrical event, time of occurrence, affected load/feeder, and overall plant impact.\n\n"
    "## 2. Single-Line Diagram (SLD) Topology & Power Flow Breakdown\n"
    "State the power delivery chain and status of each apparatus:\n"
    "- **Grid Incomer (33kV/11kV)**: [Status & Reading]\n"
    "- **11kV VCB**: [Status & Reading]\n"
    "- **Step-Down Transformer (11kV/415V Dyn11)**: [Status & Reading]\n"
    "- **LT MCC (415V)**: [Status & Reading]\n"
    "- **VFD Motor (250kW)**: [Status & Reading]\n\n"
    "## 3. High-Resolution Sequence of Events (SOE) Reconstruction\n"
    "Markdown table with columns: `Time Offset (ms)` | `Device / Asset` | `ANSI Code / Event` | `Description`.\n\n"
    "## 4. Electrical Root Cause Determination\n"
    "Detailed technical diagnosis. State specifically:\n"
    "- Primary Root Cause (e.g., Stator insulation flashover due to moisture ingress / thermal degradation)\n"
    "- Protection Operation Evaluation (Did ANSI 50N operate within expected TCC clearing time?)\n"
    "- Why upstream switchgear (11kV VCB / LT MCC Incomer) behaved as observed.\n\n"
    "## 5. Corrective & Preventive Action Plan (CAPA)\n"
    "### Immediate Restoration Steps\n"
    "- Lockout/Tagout (LOTO) isolation\n"
    "- Megger Insulation Resistance (IR) test & Polarization Index (PI)\n"
    "- VFD DC Bus & IGBT health check\n"
    "### Long-Term Preventive Recommendations\n"
    "- Relay coordination audit\n"
    "- Motor space heater verification / hermetic sealing\n"
    "- Online Partial Discharge (PD) monitoring"
)

electrical_rca_agent = Agent(
    name="ElectricalRCASummaryAgent",
    instructions=ELECTRICAL_RCA_PROMPT,
    tools=[],
    output_type=str,
    model_settings=ModelSettings(tool_choice="none")
)
