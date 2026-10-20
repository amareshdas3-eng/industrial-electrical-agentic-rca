'use client';

import React, { useState, useEffect } from 'react';

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

interface SLDVisualizationProps {
  faultedAssetTag?: string;
  selectedAssetTag?: string;
  onSelectAsset?: (node: SLDNodeData) => void;
  liveTelemetry?: {
    current_ir_amps?: number;
    voltage_v?: number;
    active_relay_flags?: string[];
    [key: string]: unknown;
  } | null;
}

export default function SLDVisualization({
  faultedAssetTag = 'MTR-VFD-01',
  selectedAssetTag,
  onSelectAsset,
  liveTelemetry
}: SLDVisualizationProps) {
  const [nodes, setNodes] = useState<SLDNodeData[]>(DEFAULT_SLD_NODES);
  const [selectedNode, setSelectedNode] = useState<SLDNodeData>(DEFAULT_SLD_NODES[4]);

  // Update nodes dynamically based on active fault
  useEffect(() => {
    const updated: SLDNodeData[] = DEFAULT_SLD_NODES.map(node => {
      if (node.tag === faultedAssetTag) {
        return {
          ...node,
          status: 'TRIPPED' as const,
          current_amps: typeof liveTelemetry?.current_ir_amps === 'number' ? liveTelemetry.current_ir_amps : node.current_amps,
          voltage_actual: '0 V (Tripped)',
          ansi_flags: Array.isArray(liveTelemetry?.active_relay_flags) ? (liveTelemetry.active_relay_flags as string[]) : node.ansi_flags
        };
      } else if (faultedAssetTag === 'GRID-INC-01' && node.tag === 'MTR-VFD-01') {
        // Consequential VFD undervoltage trip
        return {
          ...node,
          status: 'TRIPPED' as const,
          voltage_actual: '0 V (DC Undervoltage)',
          ansi_flags: ['27 (Undervoltage Trip)']
        };
      } else if (faultedAssetTag === 'TR-11KV-415V-01' && node.tag === 'TR-11KV-415V-01') {
        return {
          ...node,
          status: 'WARNING' as const,
          voltage_actual: '415 V',
          ansi_flags: ['49T Winding Temp: 118°C', '63 Buchholz: 240ml Alarm']
        };
      } else {
        return {
          ...node,
          status: 'ENERGIZED' as const
        };
      }
    });
    setNodes(updated);

    // If selectedAssetTag provided from parent, update selectedNode
    if (selectedAssetTag) {
      const match = updated.find(n => n.tag === selectedAssetTag);
      if (match) setSelectedNode(match);
    } else {
      const match = updated.find(n => n.tag === faultedAssetTag) || updated[4];
      setSelectedNode(match);
    }
  }, [faultedAssetTag, selectedAssetTag, liveTelemetry]);

  const handleNodeClick = (node: SLDNodeData) => {
    setSelectedNode(node);
    if (onSelectAsset) {
      onSelectAsset(node);
    }
  };

  return (
    <div className="w-full bg-slate-900/90 backdrop-blur-md text-white rounded-2xl shadow-2xl p-6 border border-slate-800">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 pb-4 border-b border-slate-800/80">
        <div>
          <h2 className="text-xl font-bold text-amber-400 flex items-center gap-2">
            <span>⚡</span> Electrical Single-Line Diagram (SLD) Live Power Flow
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            Hierarchy: Grid Incomer (33kV/11kV) → 11kV VCB → Step-Down Transformer → LT MCC → VFD Motor
          </p>
        </div>
        <div className="flex items-center gap-4 mt-3 md:mt-0 text-xs font-semibold">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Energized
          </span>
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span> Tripped / Isolated
          </span>
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <span className="w-2 h-2 rounded-full bg-amber-400"></span> Warning / Alarm
          </span>
        </div>
      </div>

      {/* Interactive Single-Line Diagram Canvas */}
      <div className="relative overflow-x-auto py-6 px-4 bg-slate-950/80 rounded-xl border border-slate-800 flex items-center justify-between min-w-[880px]">
        {nodes.map((node, index) => {
          const isSelected = selectedNode?.tag === node.tag;
          const isTripped = node.status === 'TRIPPED';
          const isWarning = node.status === 'WARNING';
          
          return (
            <React.Fragment key={node.id}>
              {/* SLD Equipment Node */}
              <div 
                id={`sld-node-${node.tag}`}
                onClick={() => handleNodeClick(node)}
                className={`flex flex-col items-center cursor-pointer transition-all duration-300 transform hover:-translate-y-1 p-3.5 rounded-xl border ${
                  isSelected 
                    ? 'ring-2 ring-amber-400 bg-slate-800/90 shadow-xl shadow-amber-500/10' 
                    : 'bg-slate-900/90 hover:bg-slate-800/80'
                } ${
                  isTripped 
                    ? 'border-rose-500/80 shadow-lg shadow-rose-500/20 ring-1 ring-rose-500' 
                    : isWarning
                    ? 'border-amber-500/80 shadow-lg shadow-amber-500/20'
                    : 'border-slate-700/80'
                }`}
                style={{ width: '155px' }}
              >
                {/* Visual Equipment Graphic */}
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-xl mb-2 transition-all ${
                  isTripped 
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500 animate-pulse' 
                    : isWarning
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500'
                    : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                }`}>
                  {node.type === 'Incomer' && '⚡'}
                  {node.type === 'VCB' && '⏻'}
                  {node.type === 'Transformer' && '⑂'}
                  {node.type === 'MCC' && '☰'}
                  {node.type === 'VFD_Motor' && 'Ⓜ'}
                </div>

                <span className="text-xs font-mono font-bold text-amber-300 tracking-wide">{node.tag}</span>
                <span className="text-xs font-medium text-slate-200 text-center truncate max-w-[135px] mt-0.5">
                  {node.name}
                </span>
                <span className="text-[10px] text-slate-400 mt-1 px-2 py-0.5 rounded bg-slate-950 border border-slate-800">
                  {node.voltage}
                </span>

                {/* Status Badge */}
                <div className="mt-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                    isTripped 
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' 
                      : isWarning
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                      : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                  }`}>
                    {node.status}
                  </span>
                </div>
              </div>

              {/* Power Flow Bus / Cable Arrow */}
              {index < nodes.length - 1 && (
                <div className="flex-1 flex flex-col items-center justify-center px-2">
                  <div className={`h-1.5 w-full rounded-full relative transition-colors ${
                    isTripped 
                      ? 'bg-gradient-to-r from-emerald-500 via-rose-500 to-rose-600' 
                      : 'bg-gradient-to-r from-emerald-500 to-emerald-400'
                  }`}>
                    <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0 border-t-[5px] border-t-transparent border-b-[5px] border-b-transparent border-l-[8px] border-l-emerald-400" />
                  </div>
                  <span className="text-[10px] text-slate-400 mt-1 font-mono tracking-tight">
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

      {/* Selected Apparatus Details Drawer */}
      {selectedNode && (
        <div className="mt-6 bg-slate-950/70 rounded-xl p-5 border border-slate-800 transition-all">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3 pb-3 border-b border-slate-800">
            <div>
              <span className="text-xs font-mono text-amber-400 uppercase font-bold tracking-wider">
                Telemetry & Relay Settings Inspector
              </span>
              <h3 className="text-lg font-bold text-white flex items-center gap-2 mt-0.5">
                {selectedNode.name} <span className="text-slate-400 font-mono text-xs">({selectedNode.tag})</span>
              </h3>
            </div>
            <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
              selectedNode.status === 'TRIPPED' 
                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/50' 
                : selectedNode.status === 'WARNING'
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50'
                : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50'
            }`}>
              Breaker State: {selectedNode.status}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4 text-sm">
            <div className="bg-slate-900/90 p-3.5 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 block font-medium">Rated Voltage & Capacity</span>
              <span className="text-base font-bold text-slate-100 mt-0.5 block">{selectedNode.voltage}</span>
              <span className="text-xs text-slate-400 block mt-1">{selectedNode.rating}</span>
            </div>

            <div className="bg-slate-900/90 p-3.5 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 block font-medium">Live Current & Bus Voltage</span>
              <span className={`text-base font-bold mt-0.5 block ${
                selectedNode.current_amps && selectedNode.current_amps > 1000 
                  ? 'text-rose-400 animate-pulse' 
                  : 'text-emerald-400'
              }`}>
                {selectedNode.current_amps ? `${selectedNode.current_amps.toLocaleString()} A` : 'Nominal'}
              </span>
              <span className="text-xs text-slate-400 block mt-1">Bus: {selectedNode.voltage_actual || 'Nominal'}</span>
            </div>

            <div className="bg-slate-900/90 p-3.5 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 block font-medium">Protection Relay / Device</span>
              <span className="text-base font-semibold text-amber-300 mt-0.5 block truncate">{selectedNode.relay || 'Unmetered'}</span>
              <span className="text-xs text-slate-400 block mt-1 truncate">ANSI: {selectedNode.ansi_flags?.join(', ')}</span>
            </div>

            <div className="bg-slate-900/90 p-3.5 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 block font-medium">System Role</span>
              <p className="text-xs text-slate-300 mt-1 line-clamp-2 leading-relaxed">
                {selectedNode.description}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
