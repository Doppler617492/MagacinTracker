/**
 * LocationPicker - Tree-based location selector
 * Manhattan Active WMS - Location selection component
 */
import React, { useState, useEffect } from 'react';
import './LocationPicker.css';

interface Location {
  id: string;
  naziv: string;
  code: string;
  tip: 'zone' | 'regal' | 'polica' | 'bin';
  occupancy_percentage: number;
  status_color: string;
  is_active: boolean;
  children: Location[];
}

interface LocationPickerProps {
  magacinId: string;
  zona?: string;
  onSelect: (locationId: string, locationCode: string) => void;
  selectedLocationId?: string;
}

export const LocationPicker: React.FC<LocationPickerProps> = ({
  magacinId,
  zona,
  onSelect,
  selectedLocationId
}) => {
  const [tree, setTree] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadLocationTree();
  }, [magacinId, zona]);

  const loadLocationTree = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        magacin_id: magacinId,
        ...(zona && { zona })
      });
      const response = await fetch(`/api/locations/tree?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setTree(data);
      }
    } catch (error) {
      console.error('Failed to load location tree:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleNode = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const renderNode = (location: Location, level: number = 0) => {
    const isExpanded = expandedNodes.has(location.id);
    const isSelected = location.id === selectedLocationId;
    const hasChildren = location.children && location.children.length > 0;

    return (
      <div key={location.id} className="location-node" style={{ marginLeft: `${level * 20}px` }}>
        <div 
          className={`location-node-content ${isSelected ? 'selected' : ''} ${location.tip}`}
          onClick={() => {
            if (location.tip === 'bin') {
              onSelect(location.id, location.code);
            } else if (hasChildren) {
              toggleNode(location.id);
            }
          }}
        >
          {hasChildren && (
            <span className="expand-icon">
              {isExpanded ? '▼' : '▶'}
            </span>
          )}
          <span className="location-status">{location.status_color}</span>
          <span className="location-code">{location.code}</span>
          <span className="location-naziv">{location.naziv}</span>
          {location.tip === 'bin' && (
            <span className="location-occupancy">{location.occupancy_percentage.toFixed(0)}%</span>
          )}
        </div>
        {isExpanded && hasChildren && (
          <div className="location-children">
            {location.children.map(child => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return <div className="location-picker-loading">Učitavanje lokacija...</div>;
  }

  if (tree.length === 0) {
    return <div className="location-picker-empty">Nema dostupnih lokacija</div>;
  }

  return (
    <div className="location-picker">
      <div className="location-picker-header">
        <h3>Izaberite lokaciju</h3>
      </div>
      <div className="location-picker-tree">
        {tree.map(node => renderNode(node))}
      </div>
    </div>
  );
};

