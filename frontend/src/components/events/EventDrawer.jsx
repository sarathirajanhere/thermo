import React from 'react';
import { X, Activity, ShieldCheck, MapPin, CheckCircle2 } from 'lucide-react';

export default function EventDrawer({ event, onClose, onUpdateStatus }) {
  if (!event) return null;

  const baselineDiff = event.baseline_value > 0 
    ? (((event.current_value - event.baseline_value) / event.baseline_value) * 100).toFixed(1)
    : 0;
  const isCritical = event.severity === 'CRITICAL';

  return (
    <div className="w-full lg:w-96 bg-slate-900 border border-slate-800 text-slate-100 flex flex-col h-full rounded-xl shadow-2xl z-20 font-sans">
      <div className="p-4 border-b border-slate-800 flex items-start justify-between bg-slate-950/60">
        <div>
          <span className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded uppercase ${
            isCritical ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
          }`}>
            {event.severity}
          </span>
          <h2 className="text-base font-bold mt-1 text-slate-100">{event.source_class}</h2>
          <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5 font-mono">
            <MapPin className="w-3.5 h-3.5 text-cyan-400" /> {event.facility_name || 'Non-Industrial Sector'}
          </p>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-100 p-1">
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Dynamic Baseline Comparison */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 space-y-2">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-slate-400 flex items-center gap-1">
              <Activity className="w-3.5 h-3.5 text-cyan-400" /> Dynamic Baseline
            </span>
            <span className={baselineDiff > 0 ? 'text-red-400 font-bold' : 'text-emerald-400'}>
              {baselineDiff > 0 ? `+${baselineDiff}% Anomaly` : 'Within Normal Range'}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-center font-mono">
            <div className="bg-slate-900 p-2 rounded border border-slate-800">
              <div className="text-[10px] text-slate-400">Baseline Expected</div>
              <div className="text-sm text-emerald-400 font-bold">{event.baseline_value} MW</div>
            </div>
            <div className="bg-slate-900 p-2 rounded border border-slate-800">
              <div className="text-[10px] text-slate-400">Observed FRP</div>
              <div className={`text-sm font-bold ${isCritical ? 'text-red-400' : 'text-emerald-400'}`}>
                {event.current_value} MW
              </div>
            </div>
          </div>
        </div>

        {/* Explainable AI Evidence */}
        <div className="space-y-1.5">
          <div className="text-xs font-mono text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" /> Decision Evidence
          </div>
          {event.evidence?.map((item, idx) => (
            <div key={idx} className="flex items-start gap-2 bg-slate-950/40 border border-slate-800/80 p-2 rounded text-xs text-slate-300">
              <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
              <span>{item}</span>
            </div>
          ))}
        </div>

        {/* Observation Metadata */}
        <div className="bg-slate-950/40 border border-slate-800 p-3 rounded text-xs font-mono space-y-1 text-slate-400">
          <div className="flex justify-between">
            <span>Sensor / Context</span>
            <span className="text-slate-200">{event.sensor} • {event.context_type}</span>
          </div>
          <div className="flex justify-between">
            <span>Confidence Score</span>
            <span className="text-slate-200">{(event.confidence * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex gap-2">
        <button
          onClick={() => onUpdateStatus(event.event_id, 'ACKNOWLEDGED')}
          className="flex-1 py-2 text-xs font-mono font-medium rounded bg-slate-800 hover:bg-slate-700 text-slate-200"
        >
          Acknowledge
        </button>
        <button
          onClick={() => onUpdateStatus(event.event_id, 'INVESTIGATING')}
          className="flex-1 py-2 text-xs font-mono font-bold rounded bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-600/30"
        >
          Investigate
        </button>
      </div>
    </div>
  );
}