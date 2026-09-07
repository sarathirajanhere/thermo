import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Tooltip, Polygon, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Layers } from 'lucide-react';

function MapController({ selectedEvent }) {
  const map = useMap();
  useEffect(() => {
    if (selectedEvent?.latitude && selectedEvent?.longitude) {
      map.flyTo([selectedEvent.latitude, selectedEvent.longitude], 14, { duration: 1.2 });
    }
  }, [selectedEvent, map]);
  return null;
}

const createCustomMarker = (severity, isSelected) => {
  const colorMap = {
    CRITICAL: { bg: 'bg-red-500', border: 'border-red-300', pulse: 'pulse-marker-critical' },
    HIGH: { bg: 'bg-orange-500', border: 'border-orange-300', pulse: 'pulse-marker-high' },
    MODERATE: { bg: 'bg-amber-500', border: 'border-amber-300', pulse: '' },
    LOW: { bg: 'bg-emerald-500', border: 'border-emerald-300', pulse: '' },
  };

  const current = colorMap[severity] || colorMap.LOW;
  const ring = isSelected ? 'ring-4 ring-cyan-400 scale-125' : '';

  return L.divIcon({
    html: `<div class="w-5 h-5 rounded-full ${current.bg} border-2 ${current.border} shadow-lg transition-transform ${current.pulse} ${ring}"></div>`,
    className: 'custom-marker',
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

// Demo industrial plant boundary coordinates (Manali Petrochem perimeter)
const plantBoundary = [
  [13.0880, 80.2640],
  [13.0890, 80.2760],
  [13.0780, 80.2770],
  [13.0770, 80.2650],
];

export default function MapView({ events, selectedEvent, onSelectEvent }) {
  const [mapMode, setMapMode] = useState('satellite'); // 'satellite' or 'dark'
  const defaultCenter = [13.0827, 80.2707];

  return (
    <div className="relative w-full h-full min-h-[450px] rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
      
      {/* Map Mode Switcher */}
      <div className="absolute top-4 right-4 z-[400] flex bg-slate-900/90 backdrop-blur border border-slate-700 rounded-lg p-1 font-mono text-xs shadow-xl">
        <button
          onClick={() => setMapMode('satellite')}
          className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition-all ${
            mapMode === 'satellite' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-300 hover:text-white'
          }`}
        >
          <Layers className="w-3.5 h-3.5" /> Satellite (Sentinel/Esri)
        </button>
        <button
          onClick={() => setMapMode('dark')}
          className={`px-2.5 py-1 rounded transition-all ${
            mapMode === 'dark' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-300 hover:text-white'
          }`}
        >
          Dark GIS
        </button>
      </div>

      <MapContainer center={defaultCenter} zoom={13} className="w-full h-full z-0" zoomControl={false}>
        {mapMode === 'satellite' ? (
          <TileLayer
            attribution='&copy; Esri World Imagery'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          />
        ) : (
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
        )}

        <MapController selectedEvent={selectedEvent} />

        {/* Industrial Facility Boundary Layer (OSM ground-truth) */}
        <Polygon
          positions={plantBoundary}
          pathOptions={{
            color: '#06b6d4',
            fillColor: '#0891b2',
            fillOpacity: 0.15,
            weight: 2,
            dashArray: '4, 6',
          }}
        >
          <Tooltip sticky>OSM Facility Boundary: Manali Petrochemicals</Tooltip>
        </Polygon>

        {events.map((ev) => (
          <Marker
            key={ev.event_id}
            position={[ev.latitude, ev.longitude]}
            icon={createCustomMarker(ev.severity, selectedEvent?.event_id === ev.event_id)}
            eventHandlers={{ click: () => onSelectEvent(ev) }}
          >
            <Tooltip direction="top" offset={[0, -10]} opacity={1}>
              <div className="bg-slate-900 text-slate-100 text-xs p-1.5 rounded font-mono border border-slate-700">
                <strong>[{ev.event_id}]</strong> {ev.facility_name || 'Rural Sector'} ({ev.source_class})
              </div>
            </Tooltip>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}