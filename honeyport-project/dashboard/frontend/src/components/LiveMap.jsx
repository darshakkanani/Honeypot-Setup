import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const LiveMap = () => {
  const [threatData, setThreatData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchThreatMap();
    const interval = setInterval(fetchThreatMap, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchThreatMap = async () => {
    try {
      const response = await fetch('/api/v1/threat-map', {
        headers: {
          'Authorization': 'Bearer demo-token'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setThreatData(data.threat_map || []);
      }
    } catch (error) {
      console.error('Error fetching threat map:', error);
      // Use mock data for demo
      setThreatData([
        { latitude: 39.9042, longitude: 116.4074, country: 'China', event_count: 45 },
        { latitude: 55.7558, longitude: 37.6176, country: 'Russia', event_count: 32 },
        { latitude: 40.7128, longitude: -74.0060, country: 'United States', event_count: 28 },
        { latitude: 51.5074, longitude: -0.1278, country: 'United Kingdom', event_count: 15 },
        { latitude: 35.6762, longitude: 139.6503, country: 'Japan', event_count: 12 }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getMarkerColor = (eventCount) => {
    if (eventCount > 30) return '#dc2626'; // Red for high activity
    if (eventCount > 15) return '#f59e0b'; // Orange for medium activity
    return '#10b981'; // Green for low activity
  };

  const getMarkerSize = (eventCount) => {
    return Math.max(8, Math.min(25, eventCount / 2));
  };

  if (loading) {
    return (
      <div style={{ height: '350px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div style={{ height: '350px', borderRadius: '8px', overflow: 'hidden' }}>
      <MapContainer
        center={[20, 0]}
        zoom={2}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
        scrollWheelZoom={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />
        
        {threatData.map((threat, index) => (
          <CircleMarker
            key={index}
            center={[threat.latitude, threat.longitude]}
            radius={getMarkerSize(threat.event_count)}
            fillColor={getMarkerColor(threat.event_count)}
            color={getMarkerColor(threat.event_count)}
            weight={2}
            opacity={0.8}
            fillOpacity={0.6}
          >
            <Popup>
              <div style={{ color: '#1e293b' }}>
                <strong>{threat.country}</strong><br />
                Events: {threat.event_count}<br />
                Threat Level: {threat.event_count > 30 ? 'High' : threat.event_count > 15 ? 'Medium' : 'Low'}
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
};

export default LiveMap;
