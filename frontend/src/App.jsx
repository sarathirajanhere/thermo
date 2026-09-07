import React, { useState, useEffect } from 'react';
import MapView from './map/MapView';
import StatusBar from './components/dashboard/StatusBar';
import EventDrawer from './components/events/EventDrawer';
import InvestigationModal from './components/events/InvestigationModal';
import { fetchEvents } from './api/events';
import { Flame } from 'lucide-react';

export default function App() {
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    fetchEvents().then((data) => {
      setEvents(data);
      if (data && data.length > 0) setSelectedEvent(data[0]);
    });
  }, []);

  const filteredEvents = filterSeverity === 'ALL'
    ? events
    : events.filter(e => e.severity === filterSeverity);

  const handleUpdateStatus = (id, newStatus) => {
    setEvents(prev => prev.map(e => e.event_id === id ? { ...e, status: newStatus } : e));
    if (selectedEvent?.event_id === id) {
      setSelectedEvent(prev => ({ ...prev, status: newStatus }));
    }
    if (newStatus === 'INVESTIGATING') {
      setIsModalOpen(true);
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Top Tactical Command Bar */}
      <header className="h-14 border-b border-slate-800 bg-slate-900/60 backdrop-blur px-4 flex items-center justify-between z-10 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-red-600/20 border border-red-500/40 flex items-center justify-center text-red-500">
            <Flame className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-wider uppercase font-mono text-slate-100">
              ThermoGuard <span className="text-cyan-400">AI</span>
            </h1>
            <p className="text-[10px] text-slate-400 font-mono">Team Phoenix • SIH26162</p>
          </div>
        </div>

        {/* Demo Presets for SIH Judges */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-mono mr-1 hidden sm:inline">Scenarios:</span>
          <button
            onClick={() => setSelectedEvent(events.find(e => e.event_id === 'TG-IND-0104'))}
            className="text-xs font-mono px-2.5 py-1 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300 hover:bg-emerald-900 transition-colors"
          >
            Scenario 1: Routine Flare
          </button>
          <button
            onClick={() => setSelectedEvent(events.find(e => e.event_id === 'TG-IND-0247'))}
            className="text-xs font-mono px-2.5 py-1 rounded bg-red-950/60 border border-red-800 text-red-300 hover:bg-red-900 transition-colors"
          >
            Scenario 2: Fire Anomaly
          </button>
        </div>
      </header>

      {/* Main Layout Area */}
      <main className="flex-1 flex flex-col p-3 gap-3 overflow-hidden">
        {/* KPI Counter Cards & Severity Filter Tabs */}
        <StatusBar 
          events={events} 
          currentFilter={filterSeverity} 
          onFilterChange={setFilterSeverity} 
        />

        {/* GIS Map & Event Intelligence Panel */}
        <div className="flex-1 flex overflow-hidden gap-3 relative">
          <MapView 
            events={filteredEvents} 
            selectedEvent={selectedEvent} 
            onSelectEvent={setSelectedEvent} 
          />
          {selectedEvent && (
            <EventDrawer 
              event={selectedEvent} 
              onClose={() => setSelectedEvent(null)} 
              onUpdateStatus={handleUpdateStatus} 
            />
          )}
        </div>
      </main>

      {/* Incident Protocol Dispatch Modal */}
      <InvestigationModal 
        event={selectedEvent}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
}