# Industrial Electrical Root Cause Analysis (RCA) Report

> **Standard:** IEEE C37.2 / IEC 60255 Protection & Coordination Standard  
> **Substation:** Substation-01 | **Incident:** MotorPhaseREarthFaultInstantaneousTrip  
> **Analysis Timestamp:** 2026-10-20 07:23:36 UTC  
> **Target Feeder:** MTR-VFD-01 (Boiler Feed Water Pump VFD Motor)

---

## 1. Executive Incident Summary
At `2026-10-20 11:20:00.000Z`, an instantaneous trip occurred on the **250 kW Boiler Feed Water Pump (MTR-VFD-01)**. SCADA telemetry recorded an abnormal phase current surge to **1,240.5 A** on Phase R, triggering ANSI **50N (Instantaneous Earth Fault)** and causing an immediate trip of the VFD drive's incomer MCCB (`FD-MTR-01`). The upstream distribution switchgear (**415V LT MCC-01**, **2.5 MVA Transformer TR-01**, and **11kV VCB-01**) remained energized without cascade blackout, as downstream protection successfully isolated the faulted circuit within coordination limits.

---

## 2. Single-Line Diagram (SLD) Topology & Power Flow Breakdown

The electrical power distribution hierarchy was traced from the high-voltage utility source down to the motor terminal:

```
[33kV/11kV Grid Incomer] (GRID-INC-01)
       │
       ▼ (11kV 3C x 300 mm² XLPE Cable - Status: ENERGIZED)
[11kV Vacuum Circuit Breaker] (VCB-11KV-01)
       │
       ▼ (11kV 3C x 185 mm² XLPE Cable - Status: ENERGIZED)
[Step-down Distribution Transformer 11kV/415V 2.5 MVA Dyn11] (TR-11KV-415V-01)
       │
       ▼ (3200A 4-Pole Sandwich Busduct - Status: ENERGIZED)
[415V Low Tension Motor Control Center] (MCC-415V-01)
       │
       ▼ (Feeder FD-MTR-01 - Breaker Status: TRIPPED / OPEN)
[VFD Drive & 250 kW Induction Motor] (MTR-VFD-01) [FAULT ISOLATED]
```

### Switchgear & Asset Status Matrix
- **Grid Incomer (`GRID-INC-01`)**: **ENERGIZED** | Bus Voltage: `10.82 kV` | Protection: Normal
- **11kV VCB (`VCB-11KV-01`)**: **ENERGIZED / CLOSED** | REF615 Feeder Current: `68.4 A` | 51N backup timer reset after 85 ms
- **Step-Down Transformer (`TR-11KV-415V-01`)**: **ENERGIZED** | Winding Temp: `94.5°C` (below 115°C trip) | Buchholz: Normal
- **LT MCC (`MCC-415V-01`)**: **ENERGIZED / BUS HEALTHY** | 415V Bus Voltage: `398 V` | Incomer ACB remained closed
- **VFD Motor (`MTR-VFD-01`)**: **TRIPPED / DE-ENERGIZED** | Feeder Breaker: `OPEN` | Active Trip Flags: `50N (Earth Fault)`, `49D (Drive Thermal)`

---

## 3. High-Resolution Sequence of Events (SOE) Reconstruction

Data captured by the 1-millisecond SOE Recorder reconstructed the exact sub-second chronology:

| Time Offset | Apparatus / Device | Event / ANSI Code | Functional Description |
| :--- | :--- | :--- | :--- |
| `T+000ms` | `MTR-VFD-01` | **MOTOR_STATOR_EARTH_FAULT** | Insulation flashover detected on Motor Phase R winding to frame ground (Ir = 1240A spike) |
| `T+015ms` | `RELAY-MTR-01` | **PROTECTION_PICKUP** | ANSI 50N (Instantaneous Earth Fault) pickup triggered at 1200A (> 50A threshold) |
| `T+035ms` | `RELAY-MTR-01` | **TRIP_COMMAND** | Trip command issued to VFD Incomer MCCB trip coil (94) |
| `T+042ms` | `MTR-VFD-01` | **VFD_DRIVE_FAULT** | Inverter DC Bus link protection tripped on desaturation / IGBT overcurrent protection |
| `T+065ms` | `FD-MTR-01` | **BREAKER_AUX_OPEN** | Feeder Breaker FD-MTR-01 auxiliary contact (52a) transitioned to OPEN, clearing fault from LT MCC |
| `T+080ms` | `MCC-415V-01` | **VOLTAGE_RECOVERY** | LT MCC Bus voltage restored to 415V nominal after fault clearance |
| `T+085ms` | `VCB-11KV-01` | **PROTECTION_RESET** | Upstream 11kV VCB relay REF615 51N backup timer reset (fault cleared downstream within coordination margin) |

---

## 4. Electrical Root Cause Determination

### 4.1 Primary Root Cause
- **Dielectric Insulation Breakdown (Phase R Stator Winding):**
  Correlating the fault surge of **1,240.5 A** on Phase R with historical test records reveals that the motor's insulation resistance had severely degraded to **3.2 MΩ** (down from its 150 MΩ baseline). Micro-cracks in the stator slot insulation combined with thermal cycling and ambient humidity caused an electrical flashover to the earthed stator core.
- **VFD IGBT Protection Response:**
  The steep $di/dt$ transient triggered the drive's desaturation protection within 42 milliseconds, safeguarding the inverter bridge from catastrophic silicon rupture.

### 4.2 Protection Coordination Assessment (ANSI / IEEE C37.2)
- **Selectivity Evaluation:** **PASS (Properly Coordinated)**.
  The local feeder protection `RELAY-MTR-01` operated instantaneously (50N at $T+15$ ms) and cleared the fault via MCCB trip coil (94) in **65 ms total clearing time**.
- **Upstream Backup Discrimination:**
  The upstream 11kV VCB relay (`ABB REF615`) picked up its 51N IDMT timer at $T+0$ ms, set for 180 ms coordination delay. Because the downstream breaker extinguished the fault arc in 65 ms, the 11kV VCB relay automatically reset at $T+85$ ms, successfully preventing an uncoordinated cascade outage of the entire 415V MCC bus.

---

## 5. Corrective & Preventive Action Plan (CAPA)

### Immediate Restoration Actions
1. **Apply Lockout/Tagout (LOTO):** Rack out feeder breaker `FD-MTR-01` on LT MCC panel; apply padlock and warning tags per OSHA/NFPA 70E.
2. **Offline Megger & Polarization Index (PI) Test:** Conduct 1,000V DC Insulation Resistance test on Motor Phase R, Y, B to ground and phase-to-phase. Confirm if fault is in motor terminals or internal winding.
3. **Surge Comparison & Surge Voltage Test:** Check stator turns for inter-turn short circuits.
4. **VFD Inverter Stage Diode/IGBT Check:** Measure forward voltage drop of IGBT antiparallel diodes using digital multimeter.

### Long-Term Preventive Measures
1. **Motor Rewinding / Varnish Dip:** Strip and rewind Phase R stator winding with Class H inverter-grade Nomex insulation.
2. **Space Heater Interlocking:** Verify that the motor anti-condensation space heaters automatically energize when the motor is stopped.
3. **Install dV/dt or Sine-Wave Filter:** Fit an output dV/dt reactor between the VFD and motor to reduce peak voltage reflection spikes ($V_{peak} > 1200V$) on the winding insulation.
4. **Relay Coordination Record Update:** Archive this SOE timing trace to validate future protective relay setting studies.
