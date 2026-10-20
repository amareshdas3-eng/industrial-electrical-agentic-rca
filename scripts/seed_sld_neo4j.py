"""
Seed script to populate Neo4j with the Industrial Electrical Single-Line Diagram (SLD) topology:
Grid Incomer -> 11kV VCB -> Step-down Transformer -> LT MCC -> VFD Motor
"""

import os
import json
from typing import Dict, Any, List

CYPHER_SEED_STATEMENTS = [
    # Clean previous SLD nodes
    "MATCH (n:ElectricalAsset) DETACH DELETE n",
    
    # 1. Grid Incomer Node
    """
    CREATE (inc:ElectricalAsset {
        asset_tag: "GRID-INC-01",
        name: "33kV/11kV Utility Grid Incomer",
        asset_type: "UtilityIncomer",
        voltage_level: "11kV",
        rated_capacity: "40 MVA Fault Level",
        operating_status: "ENERGIZED",
        location: "Outdoor Switchyard",
        relay_tag: "RELAY-GRID-01",
        relay_type: "Siemens 7SJ82 Feeder Protection",
        ansi_codes: "50,51,50N,51N,27,59,81",
        last_trip_flag: "NORMAL"
    })
    """,
    
    # 2. 11kV VCB Node
    """
    CREATE (vcb:ElectricalAsset {
        asset_tag: "VCB-11KV-01",
        name: "11kV Vacuum Circuit Breaker (Feeder 1)",
        asset_type: "VCB",
        voltage_level: "11kV",
        rated_capacity: "1250 A / 25 kA Breaking",
        operating_status: "ENERGIZED",
        location: "11kV Indoor Switchgear Room",
        relay_tag: "RELAY-VCB-01",
        relay_type: "ABB REF615 Numerical Feeder Protection",
        ansi_codes: "50,51,50N,51N",
        pickup_current: "1.0x In (1250A)",
        time_multiplier_tms: "0.15",
        last_trip_flag: "NORMAL"
    })
    """,
    
    # 3. Step-down Transformer Node
    """
    CREATE (tr:ElectricalAsset {
        asset_tag: "TR-11KV-415V-01",
        name: "Step-down Distribution Transformer (TR-1)",
        asset_type: "Transformer",
        voltage_level: "11kV/415V",
        rated_capacity: "2500 kVA (2.5 MVA)",
        operating_status: "ENERGIZED",
        location: "Transformer Yard Bay 1",
        vector_group: "Dyn11",
        impedance_percent: "6.25%",
        cooling_type: "ONAN",
        relay_tag: "RELAY-TR-01",
        relay_type: "Transformer Protection Unit",
        ansi_codes: "49T,49OT,63,87T,51N",
        last_trip_flag: "NORMAL"
    })
    """,
    
    # 4. LT MCC Node
    """
    CREATE (mcc:ElectricalAsset {
        asset_tag: "MCC-415V-01",
        name: "415V Low Tension Motor Control Center (MCC-1)",
        asset_type: "MCC",
        voltage_level: "415V",
        rated_capacity: "3200 A Busbar / 50 kA Fault Withstand",
        operating_status: "ENERGIZED",
        location: "LT Switchgear Room",
        incomer_device: "ACB 3200A 4-Pole Drawout",
        relay_tag: "RELAY-MCC-INCOMER",
        relay_type: "Microprocessor Trip Unit (LSIG)",
        ansi_codes: "50,51,51N,27",
        last_trip_flag: "NORMAL"
    })
    """,
    
    # 5. VFD Motor Load Node
    """
    CREATE (mtr:ElectricalAsset {
        asset_tag: "MTR-VFD-01",
        name: "Boiler Feed Water Pump VFD Motor",
        asset_type: "VFD_Motor",
        voltage_level: "415V",
        rated_capacity: "250 kW / 410 A FLC",
        operating_status: "ENERGIZED",
        location: "Boiler House Floor 1",
        drive_model: "ABB ACS880 250kW 6-Pulse IGBT",
        motor_type: "3-Phase Squirrel Cage Induction Motor (Class F/B)",
        feeder_breaker: "MCCB 630A with Thermal-Magnetic Release",
        relay_tag: "RELAY-MTR-01",
        relay_type: "Integrated VFD Protection + REM615",
        ansi_codes: "49,50,50N,51LR,27,38",
        last_trip_flag: "NORMAL"
    })
    """,
    
    # Relationships representing electrical power flow (FEEDS)
    """
    MATCH (inc:ElectricalAsset {asset_tag: "GRID-INC-01"}), (vcb:ElectricalAsset {asset_tag: "VCB-11KV-01"})
    CREATE (inc)-[:FEEDS {
        voltage: "11kV",
        cable_spec: "3C x 300 sq.mm XLPE Al Armoured",
        rated_current: "1250A",
        breaker_status: "CLOSED",
        power_flow_direction: "DOWNSTREAM"
    }]->(vcb)
    """,
    
    """
    MATCH (vcb:ElectricalAsset {asset_tag: "VCB-11KV-01"}), (tr:ElectricalAsset {asset_tag: "TR-11KV-415V-01"})
    CREATE (vcb)-[:FEEDS {
        voltage: "11kV",
        cable_spec: "3C x 185 sq.mm XLPE Cu Cable",
        rated_current: "630A",
        breaker_status: "CLOSED",
        power_flow_direction: "DOWNSTREAM"
    }]->(tr)
    """,
    
    """
    MATCH (tr:ElectricalAsset {asset_tag: "TR-11KV-415V-01"}), (mcc:ElectricalAsset {asset_tag: "MCC-415V-01"})
    CREATE (tr)-[:FEEDS {
        voltage: "415V",
        cable_spec: "3200A 4-Pole Sandwich Aluminium Busduct",
        rated_current: "3200A",
        breaker_status: "CLOSED",
        power_flow_direction: "DOWNSTREAM"
    }]->(mcc)
    """,
    
    """
    MATCH (mcc:ElectricalAsset {asset_tag: "MCC-415V-01"}), (mtr:ElectricalAsset {asset_tag: "MTR-VFD-01"})
    CREATE (mcc)-[:FEEDS {
        voltage: "415V",
        cable_spec: "3.5C x 300 sq.mm XLPE Cu Flexible Drive Cable",
        rated_current: "630A",
        breaker_status: "CLOSED",
        feeder_tag: "FD-MTR-01",
        power_flow_direction: "DOWNSTREAM"
    }]->(mtr)
    """
]

# Static In-Memory Graph Definition (Fallback when Neo4j is offline)
IN_MEMORY_SLD_GRAPH = {
    "nodes": {
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
                "pickup_current": "1.0x In (1250A)",
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
                "cooling": "ONAN",
                "primary_flc_amps": 131.2,
                "secondary_flc_amps": 3478.0
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
                "motor_type": "3-Phase Squirrel Cage Induction Motor (Class F/B)",
                "feeder_breaker": "MCCB 630A Thermal-Magnetic",
                "rpm": 1485
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
}

def seed_neo4j():
    """Attempt to seed Neo4j if available, or write the in-memory json cache."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    print(f"Connecting to Neo4j at {uri}...")
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(uri, auth=(username, password))
        with driver.session() as session:
            for stmt in CYPHER_SEED_STATEMENTS:
                session.run(stmt)
        driver.close()
        print(" Successfully seeded Neo4j with Industrial Electrical SLD Topology!")
    except Exception as e:
        print(f" Notice: Neo4j server not currently active at {uri}: {e}")
        print(" Saving in-memory SLD topology fallback data to 'scripts/sld_graph_cache.json'...")
        os.makedirs("scripts", exist_ok=True)
        with open("scripts/sld_graph_cache.json", "w") as f:
            json.dump(IN_MEMORY_SLD_GRAPH, f, indent=2)
        print(" Saved in-memory SLD graph cache.")

if __name__ == "__main__":
    seed_neo4j()
