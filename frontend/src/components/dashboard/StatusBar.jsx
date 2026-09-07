import React from 'react';
import { Flame, AlertTriangle, ShieldCheck, Factory } from 'lucide-react';

export default function StatusBar({ events, currentFilter, onFilterChange }) {
  const totalEvents = events.length;
  const criticalCount = events.filter(e => e.severity === 'CRITICAL').length;
  const industrialCount = events.filter(e => e.context_type === 'Industrial Facility').length;
  const routineCount = events.filter(e => e.severity === 'LOW').length;

  return (
    <div className="space-y-3 shrink-0">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono">
        <div className="bg-slate-900/70 border border-slate-800 p-3 rounded-lg flex items-center gap-3">
          <Flame className="w-6 h-6 text-cyan-400" />
          <div>
            <div className="text-[10px] text-slate-400 uppercase">Active Hotspots</div>
            <div className="text-xl font-bold text-slate-100">{totalEvents}</div>
          </div>
        </div>
        <div className="bg-slate-900/70 border border-slate-800 p-3 rounded-lg flex items-center gap-3">
          <Factory className="w-6 h-6 text-indigo-400" />
          <div>
            <div className="text-[10px] text-slate-400 uppercase">Industrial Sites</div>
            <div className="text-xl font-bold text-slate-100">{industrialCount}</div>
          </div>
        </div>
        <div className="bg-slate-900/70 border border-slate-800 p-3 rounded-lg flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 text-red-400" />
          <div>
            <div className="text-[10px] text-slate-400 uppercase">Critical Anomalies</div>
            <div className="text-xl font-bold text-red-400">{criticalCount}</div>
          </div>
        </div>
        <div className="bg-slate-900/70 border border-slate-800 p-3 rounded-lg flex items-center gap-3">
          <ShieldCheck className="w-6 h-6 text-emerald-400" />
          <div>
            <div className="text-[10px] text-slate-400 uppercase">Routine Baseline</div>
            <div className="text-xl font-bold text-emerald-400">{routineCount}</div>
          </div>
        </div>
      </div>

      <div className="flex gap-2 text-xs font-mono">
        {['ALL', 'CRITICAL', 'HIGH', 'MODERATE', 'LOW'].map((sev) => (
          <button
            key={sev}
            onClick={() => onFilterChange(sev)}
            className={`px-3 py-1 rounded transition-colors ${
              currentFilter === sev 
                ? 'bg-cyan-500 text-slate-950 font-bold' 
                : 'bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800'
            }`}
          >
            {sev}
          </button>
        ))}
      </div>
    </div>
  );
}