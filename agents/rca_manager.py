"""
Industrial Electrical Root Cause Analysis Manager.
Primary orchestrator for SLD topology traversal, IED telemetry, 1ms SOE logs, and IEEE/IEC RCA reports.
"""

from electrical_rca_manager import ElectricalRCAManager

# Primary manager class
RCA_Manager = ElectricalRCAManager

__all__ = ["RCA_Manager", "ElectricalRCAManager"]