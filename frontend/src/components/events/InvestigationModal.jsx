import React from 'react';
import { X, AlertOctagon, PhoneCall, ShieldAlert, FileText, CheckCircle } from 'lucide-react';

export default function InvestigationModal({ event, isOpen, onClose }) {
  if (!isOpen || !event) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 font-sans">
      <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-xl overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-150">
        
        {/* Header */}
        <div className="p-4 bg-red-950/40 border-b border-red-900/50 flex items-center justify-between">
          <div className="flex items-center gap-2 text-red-400 font-mono font-bold text-sm">
            <AlertOctagon className="w-5 h-5" />
            INCIDENT PROTOCOL — {event.event_id}
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 text-xs font-mono text-slate-300">
          <div className="bg-slate-950 p-3 rounded border border-slate-800 space-y-1">
            <div className="text-slate-400">Target Facility: <span className="text-slate-100 font-bold">{event.facility_name}</span></div>
            <div className="text-slate-400">Deviation: <span className="text-red-400 font-bold">+{(((event.current_value - event.baseline_value) / event.baseline_value) * 100).toFixed(1)}% above dynamic baseline</span></div>
            <div className="text-slate-400">Coordinates: <span className="text-cyan-400">{event.latitude}, {event.longitude}</span></div>
          </div>

          <div className="space-y-2">
            <div className="text-slate-400 uppercase tracking-wider text-[11px] font-bold">Standard Operating Procedures:</div>
            <div className="flex items-center gap-2 p-2 bg-slate-950/60 rounded border border-slate-800">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              <span>Automated alert dispatched to On-Site Fire Safety Officer</span>
            </div>
            <div className="flex items-center gap-2 p-2 bg-slate-950/60 rounded border border-slate-800">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              <span>Pollution Control Board audit log entry generated</span>
            </div>
            <div className="flex items-center gap-2 p-2 bg-slate-950/60 rounded border border-slate-800">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <span>Perimeter gas dispersion buffer zone flagged (2.5 km)</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="p-4 bg-slate-950/80 border-t border-slate-800 flex justify-end gap-2 font-mono text-xs">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded bg-slate-800 hover:bg-slate-700 text-slate-200"
          >
            Close
          </button>
          <button
            onClick={() => {
              alert(`Emergency Protocol Triggered for ${event.facility_name}`);
              onClose();
            }}
            className="px-4 py-2 rounded bg-red-600 hover:bg-red-500 font-bold text-white shadow-lg shadow-red-600/30 flex items-center gap-1.5"
          >
            <PhoneCall className="w-3.5 h-3.5" /> Dispatch Emergency Alert
          </button>
        </div>

      </div>
    </div>
  );
}