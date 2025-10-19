/**
 * WarehouseMapView - 2D warehouse visualization
 * Manhattan Active WMS - Vizualna mapa magacina
 */
import React, { useState, useEffect, useRef } from 'react';
import { Select, Spin, Card } from 'antd';
import './WarehouseMapView.css';

const { Option } = Select;

interface MapLocation {
  id: string;
  code: string;
  naziv: string;
  tip: 'zone' | 'regal' | 'polica' | 'bin';
  x: number;
  y: number;
  occupancy_percentage: number;
  status_color: string;
  is_active: boolean;
}

interface WarehouseMap {
  magacin_id: string;
  magacin_naziv: string;
  locations: MapLocation[];
  zones: string[];
  last_updated: string;
}

export const WarehouseMapView: React.FC = () => {
  const [map, setMap] = useState<WarehouseMap | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedZone, setSelectedZone] = useState<string | undefined>();
  const [hoveredLocation, setHoveredLocation] = useState<MapLocation | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    loadWarehouseMap();
    const interval = setInterval(loadWarehouseMap, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [selectedZone]);

  useEffect(() => {
    if (map) {
      drawMap();
    }
  }, [map, hoveredLocation]);

  const loadWarehouseMap = async () => {
    try {
      setLoading(true);
      const magacinId = localStorage.getItem('current_magacin_id') || '';
      const params = new URLSearchParams({
        magacin_id: magacinId,
        ...(selectedZone && { zona: selectedZone })
      });
      
      const response = await fetch(`/api/locations/warehouse-map?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMap(data);
      }
    } catch (error) {
      console.error('Failed to load warehouse map:', error);
    } finally {
      setLoading(false);
    }
  };

  const drawMap = () => {
    const canvas = canvasRef.current;
    if (!canvas || !map) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Find bounds
    const locations = map.locations;
    if (locations.length === 0) return;

    const minX = Math.min(...locations.map(l => l.x));
    const maxX = Math.max(...locations.map(l => l.x));
    const minY = Math.min(...locations.map(l => l.y));
    const maxY = Math.max(...locations.map(l => l.y));

    const padding = 40;
    const scaleX = (canvas.width - 2 * padding) / (maxX - minX || 1);
    const scaleY = (canvas.height - 2 * padding) / (maxY - minY || 1);
    const scale = Math.min(scaleX, scaleY);

    // Draw grid
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;
    for (let x = minX; x <= maxX; x += 5) {
      const canvasX = padding + (x - minX) * scale;
      ctx.beginPath();
      ctx.moveTo(canvasX, padding);
      ctx.lineTo(canvasX, canvas.height - padding);
      ctx.stroke();
    }
    for (let y = minY; y <= maxY; y += 5) {
      const canvasY = padding + (y - minY) * scale;
      ctx.beginPath();
      ctx.moveTo(padding, canvasY);
      ctx.lineTo(canvas.width - padding, canvasY);
      ctx.stroke();
    }

    // Draw locations
    locations.forEach(loc => {
      const x = padding + (loc.x - minX) * scale;
      const y = padding + (loc.y - minY) * scale;
      const size = getSizeForType(loc.tip, scale);

      // Color based on occupancy
      const color = getColorForOccupancy(loc.occupancy_percentage);
      ctx.fillStyle = color;
      ctx.fillRect(x - size / 2, y - size / 2, size, size);

      // Border
      ctx.strokeStyle = hoveredLocation?.id === loc.id ? '#1976d2' : '#1a1a1a';
      ctx.lineWidth = hoveredLocation?.id === loc.id ? 3 : 1;
      ctx.strokeRect(x - size / 2, y - size / 2, size, size);

      // Label (for bins)
      if (loc.tip === 'bin') {
        ctx.fillStyle = '#1a1a1a';
        ctx.font = `${Math.max(8, scale * 0.5)}px monospace`;
        ctx.textAlign = 'center';
        ctx.fillText(loc.code, x, y + size / 2 + 12);
      }
    });
  };

  const getSizeForType = (tip: string, scale: number) => {
    const sizes = {
      zone: scale * 10,
      regal: scale * 5,
      polica: scale * 3,
      bin: scale * 2
    };
    return sizes[tip as keyof typeof sizes] || scale * 2;
  };

  const getColorForOccupancy = (percentage: number) => {
    if (percentage >= 90) return '#ef5350'; // Red
    if (percentage >= 50) return '#ffa726'; // Orange
    return '#66bb6a'; // Green
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || !map) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Find location under cursor
    const locations = map.locations;
    const minX = Math.min(...locations.map(l => l.x));
    const maxX = Math.max(...locations.map(l => l.x));
    const minY = Math.min(...locations.map(l => l.y));
    const maxY = Math.max(...locations.map(l => l.y));

    const padding = 40;
    const scaleX = (canvas.width - 2 * padding) / (maxX - minX || 1);
    const scaleY = (canvas.height - 2 * padding) / (maxY - minY || 1);
    const scale = Math.min(scaleX, scaleY);

    let found: MapLocation | null = null;
    for (const loc of locations) {
      const x = padding + (loc.x - minX) * scale;
      const y = padding + (loc.y - minY) * scale;
      const size = getSizeForType(loc.tip, scale);

      if (
        mouseX >= x - size / 2 &&
        mouseX <= x + size / 2 &&
        mouseY >= y - size / 2 &&
        mouseY <= y + size / 2
      ) {
        found = loc;
        break;
      }
    }

    setHoveredLocation(found);
  };

  return (
    <div className="warehouse-map-view">
      <div className="map-header">
        <h2>{map?.magacin_naziv || 'Mapa magacina'}</h2>
        <Select
          placeholder="Sve zone"
          allowClear
          style={{ width: 150 }}
          onChange={setSelectedZone}
          value={selectedZone}
        >
          {map?.zones.map(zone => (
            <Option key={zone} value={zone}>Zona {zone}</Option>
          ))}
        </Select>
      </div>

      {loading ? (
        <div className="map-loading">
          <Spin size="large" />
          <p>Učitavanje mape...</p>
        </div>
      ) : (
        <>
          <canvas
            ref={canvasRef}
            width={1200}
            height={800}
            className="warehouse-canvas"
            onMouseMove={handleCanvasMouseMove}
            onMouseLeave={() => setHoveredLocation(null)}
          />

          {hoveredLocation && (
            <Card className="location-tooltip" size="small">
              <div className="tooltip-content">
                <div className="tooltip-header">
                  <strong>{hoveredLocation.code}</strong>
                  <span>{hoveredLocation.naziv}</span>
                </div>
                <div className="tooltip-body">
                  <div className="tooltip-field">
                    <span>Popunjenost:</span>
                    <strong>{hoveredLocation.occupancy_percentage.toFixed(0)}%</strong>
                  </div>
                </div>
              </div>
            </Card>
          )}

          <div className="map-legend">
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#66bb6a' }}></div>
              <span>Slobodno (&lt; 50%)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#ffa726' }}></div>
              <span>Delimično (50-90%)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#ef5350' }}></div>
              <span>Puno (≥ 90%)</span>
            </div>
          </div>

          <div className="map-stats">
            <div className="stat-card">
              <div className="stat-value">{map?.locations.length || 0}</div>
              <div className="stat-label">Ukupno lokacija</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">
                {map?.locations.filter(l => l.occupancy_percentage < 50).length || 0}
              </div>
              <div className="stat-label">Slobodno</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">
                {map?.locations.filter(l => l.occupancy_percentage >= 90).length || 0}
              </div>
              <div className="stat-label">Puno</div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

