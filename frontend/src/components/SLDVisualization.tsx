'use client';

import React, { useState } from 'react';

export interface SLDNodeData {
  id: string;
  tag: string;
  name: string;
  voltage: string;
  type: 'Incomer' | 'VCB' | 'Transformer' | 'MCC' | 'VFD_Motor';
  rating: string;
  status: 'ENERGIZED' | 'TRIPPED' | 'WARNING';
  current_amps?: number;
  voltage_actual?: string;
  relay?: string;
  ansi_flags?: string[];
  description: string;
}

const DEFAULT_SLD_NODES: SLDNodeData[] = [
  {
    id: '1',
    tag: 'GRID-INC-01',
    name: 'Utility Grid Incomer',
    voltage: '33kV / 11kV',
    type: 'Incomer',
    rating: '40 MVA Fault Level',
    status: 'ENERGIZED',
    voltage_actual: '10.82 kV',
    current_amps: 68.4,
    relay: 'Siemens 7SJ82',
    ansi_flags: ['Normal'],
    description: 'Main utility high-voltage feeder supplying the substation primary switchyard.'
  },
  {
    id: '2',
    tag: 'VCB-11KV-01',
    name: '11kV Vacuum Circuit Breaker',
    voltage: '11kV',
    type: 'VCB',
    rating: '1250A / 25kA',
    status: 'ENERGIZED',
    voltage_actual: '11.0 kV',
    current_amps: 68.4,
    relay: 'ABB REF615',
    ansi_flags: ['51N Backup Armed (Reset at 85ms)'],
    description: 'Indoor medium-voltage circuit breaker feeding the primary side of distribution transformer TR-1.'
  },
  {
    id: '3',
    tag: 'TR-11KV-415V-01',
    name: 'Step-Down Distribution Transformer',
    voltage: '11kV / 415V',
    type: 'Transformer',
    rating: '2500 kVA (Dyn11, 6.25% Z)',
    status: 'ENERGIZED',
    voltage_actual: '415 V',
    current_amps: 1820,
    relay: 'Buchholz (63) + WTI (49T)',
    ansi_flags: ['49T Winding Temp: 94.5°C'],
    description: 'Oil-immersed ONAN transformer stepping down 11kV distribution voltage to 415V utilization level.'
  },
  {
    id: '4',
    tag: 'MCC-415V-01',
    name: '415V Low Tension Motor Control Center',
    voltage: '415V',
    type: 'MCC',
    rating: '3200A Busbar / 50kA',
    status: 'ENERGIZED',
    voltage_actual: '398 V (Recovered)',
    current_amps: 1820,
    relay: 'LSIG Microprocessor Trip Unit',
    ansi_flags: ['Bus Voltage Nominal'],
    description: 'Main low-tension switchboard distributing power to industrial motor drives and auxiliary panels.'
  },
  {
    id: '5',
    tag: 'MTR-VFD-01',
    name: 'Boiler Feed Water Pump VFD Motor',
    voltage: '415V',
    type: 'VFD_Motor',
    rating: '250 kW / 410A FLC',
    status: 'TRIPPED',
    voltage_actual: '0 V (Breaker Open)',
    current_amps: 1240.5,
    relay: 'Integrated Drive Protection + REM615',
    ansi_flags: ['50N Instantaneous Earth Fault', '49D Drive Thermal Overload'],
    description: 'Critical variable-speed motor driven by a 6-pulse IGBT inverter. Tripped on Phase R stator earth fault.'
  }
];

export default function SLDVisualization() {
  const [nodes] = useState<SLDNodeData[]>(DEFAULT_SLD_NODES);
  const [selectedNode, setSelectedNode] = useState<SLDNodeData>(DEFAULT_SLD_NODES[4]);

  return (
    <div className="w-full bg-slate-900 text-white rounded-xl shadow-2xl p-6 border border-slate-700">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-2xl font-bold text-amber-400 flex items-center gap-2">
            <span>⚡</span> Industrial Electrical Single-Line Diagram (SLD)
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Power Flow Topology: Grid Incomer → 11kV VCB → Step-down Transformer → LT MCC → VFD Motor
          </p>
        </div>
        <div className="flex items-center gap-4 mt-3 md:mt-0 text-xs font-semibold">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></span> Energized
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-rose-500 animate-ping"></span> Tripped / Fault
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-amber-500"></span> Warning
          </span>
        </div>
      </div>

      {/* Interactive Single-Line Diagram Diagram */}
      <div className="relative overflow-x-auto py-8 px-4 bg-slate-950/70 rounded-lg border border-slate-800 flex items-center justify-between min-w-[900px]">
        {nodes.map((node, index) => {
          const isSelected = selectedNode?.id === node.id;
          const isTripped = node.status === 'TRIPPED';
          
          return (
            <React.Fragment key={node.id}>
              {/* SLD Node Box */}
              <div 
                onClick={() => setSelectedNode(node)}
                className={`flex flex-col items-center cursor-pointer transition-all duration-200 transform hover:scale-105 p-3 rounded-xl border ${
                  isSelected 
                    ? 'ring-2 ring-amber-400 bg-slate-800/90 shadow-lg shadow-amber-400/20' 
                    : 'bg-slate-800/50 hover:bg-slate-800/70'
                } ${
                  isTripped 
                    ? 'border-rose-500 shadow-rose-500/20' 
                    : 'border-slate-700'
                }`}
                style={{ width: '160px' }}
              >
                {/* Node Symbol Graphic */}
                <div className={`w-14 h-14 rounded-lg flex items-center justify-center font-bold text-xl mb-2 ${
                  isTripped 
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500 animate-bounce' 
                    : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500'
                }`}>
                  {node.type === 'Incomer' && '⚡'}
                  {node.type === 'VCB' && '⏻'}
                  {node.type === 'Transformer' && '⑂'}
                  {node.type === 'MCC' && '☰'}
                  {node.type === 'VFD_Motor' && 'Ⓜ'}
                </div>

                <span className="text-xs font-mono font-bold text-amber-300">{node.tag}</span>
                <span className="text-xs font-medium text-slate-200 text-center truncate max-w-[140px] mt-0.5">
                  {node.name}
                </span>
                <span className="text-[10px] text-slate-400 mt-1 px-2 py-0.5 rounded bg-slate-900 border border-slate-700">
                  {node.voltage}
                </span>

                {/* Status Badge */}
                <div className="mt-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                    isTripped 
                      ? 'bg-rose-500/30 text-rose-300 border border-rose-500/50' 
                      : 'bg-emerald-500/30 text-emerald-300 border border-emerald-500/50'
                  }`}>
                    {node.status}
                  </span>
                </div>
              </div>

              {/* Power Flow Connecting Bus / Cable Arrow */}
              {index < nodes.length - 1 && (
                <div className="flex-1 flex flex-col items-center justify-center px-2">
                  <div className="h-1 w-full bg-gradient-to-r from-emerald-500 via-amber-400 to-emerald-500 rounded relative">
                    <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0 border-t-4 border-t-transparent border-b-4 border-b-transparent border-l-8 border-l-emerald-400" />
                  </div>
                  <span className="text-[10px] text-slate-400 mt-1 font-mono">
                    {index === 0 && '11kV Feeder'}
                    {index === 1 && '11kV Cable'}
                    {index === 2 && '3200A Busduct'}
                    {index === 3 && 'Drive Cable'}
                  </span>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Selected Node Details Card */}
      {selectedNode && (
        <div className="mt-6 bg-slate-800/80 rounded-xl p-5 border border-slate-700">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3 pb-3 border-b border-slate-700">
            <div>
              <span className="text-xs font-mono text-amber-400 uppercase font-bold tracking-wider">
                Asset Telemetry & Engineering Specs
              </span>
              <h3 className="text-xl font-bold text-white flex items-center gap-2 mt-0.5">
                {selectedNode.name} <span className="text-slate-400 font-mono text-sm">({selectedNode.tag})</span>
              </h3>
            </div>
            <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
              selectedNode.status === 'TRIPPED' 
                ? 'bg-rose-500/30 text-rose-300 border border-rose-500' 
                : 'bg-emerald-500/30 text-emerald-300 border border-emerald-500'
            }`}>
              Status: {selectedNode.status}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4 text-sm">
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-xs text-slate-400 block">Rated Voltage & Capacity</span>
              <span className="text-base font-semibold text-slate-100">{selectedNode.voltage}</span>
              <span className="text-xs text-slate-400 block mt-1">{selectedNode.rating}</span>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-xs text-slate-400 block">Live Current Reading</span>
              <span className={`text-base font-bold ${
                selectedNode.current_amps && selectedNode.current_amps > 1000 
                  ? 'text-rose-400 animate-pulse' 
                  : 'text-emerald-400'
              }`}>
                {selectedNode.current_amps ? `${selectedNode.current_amps} A` : 'N/A'}
              </span>
              <span className="text-xs text-slate-400 block mt-1">Bus: {selectedNode.voltage_actual || 'Nominal'}</span>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-xs text-slate-400 block">Protection Relay / Device</span>
              <span className="text-base font-semibold text-amber-300">{selectedNode.relay || 'Unmetered'}</span>
              <span className="text-xs text-slate-400 block mt-1">ANSI Codes: {selectedNode.ansi_flags?.join(', ')}</span>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-xs text-slate-400 block">Functional Role</span>
              <p className="text-xs text-slate-300 mt-1 line-clamp-3 leading-relaxed">
                {selectedNode.description}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
