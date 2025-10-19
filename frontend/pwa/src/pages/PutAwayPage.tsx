/**
 * PutAwayPage - Directed put-away with AI suggestions
 * Manhattan Active WMS - Vođeno skladištenje
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { LocationPicker } from '../components/LocationPicker';
import './PutAwayPage.css';

interface Suggestion {
  location_id: string;
  location_code: string;
  location_naziv: string;
  score: number;
  distance_meters?: number;
  available_capacity: number;
  occupancy_percentage: number;
  reason: string;
}

interface ReceivingItem {
  id: string;
  artikal_sifra: string;
  artikal_naziv: string;
  kolicina_trazena: number;
  kolicina_primljena: number;
  jm: string;
  suggested_location_id?: string;
}

export const PutAwayPage: React.FC = () => {
  const { itemId } = useParams<{ itemId: string }>();
  const navigate = useNavigate();
  
  const [item, setItem] = useState<ReceivingItem | null>(null);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [showManualPicker, setShowManualPicker] = useState(false);
  const [selectedLocationId, setSelectedLocationId] = useState<string | null>(null);
  const [selectedLocationCode, setSelectedLocationCode] = useState<string>('');
  const [executing, setExecuting] = useState(false);

  useEffect(() => {
    loadItemAndSuggestions();
  }, [itemId]);

  const loadItemAndSuggestions = async () => {
    try {
      setLoading(true);
      // Load receiving item details
      const itemResponse = await fetch(`/api/receiving/items/${itemId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (itemResponse.ok) {
        const itemData = await itemResponse.json();
        setItem(itemData);
        
        // Load AI suggestions
        const suggestionResponse = await fetch('/api/locations/putaway/suggest', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            artikal_id: itemData.artikal_id,
            quantity: itemData.kolicina_primljena,
            uom: itemData.jm
          })
        });
        
        if (suggestionResponse.ok) {
          const suggestionData = await suggestionResponse.json();
          setSuggestions(suggestionData.suggestions);
          if (suggestionData.suggestions.length > 0) {
            setSelectedLocationId(suggestionData.suggestions[0].location_id);
            setSelectedLocationCode(suggestionData.suggestions[0].location_code);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load put-away data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExecutePutAway = async () => {
    if (!selectedLocationId || !item) return;
    
    try {
      setExecuting(true);
      const response = await fetch('/api/locations/putaway/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          receiving_item_id: item.id,
          location_id: selectedLocationId,
          quantity: item.kolicina_primljena,
          override_suggestion: showManualPicker
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`✅ ${result.message}`);
        navigate('/receiving');
      } else {
        const error = await response.json();
        alert(`❌ ${error.detail}`);
      }
    } catch (error) {
      console.error('Failed to execute put-away:', error);
      alert('❌ Greška pri skladištenju');
    } finally {
      setExecuting(false);
    }
  };

  if (loading) {
    return <div className="putaway-loading">Učitavanje...</div>;
  }

  if (!item) {
    return <div className="putaway-error">Stavka ne postoji</div>;
  }

  return (
    <div className="putaway-page">
      <div className="putaway-header">
        <button className="back-button" onClick={() => navigate(-1)}>
          ← Nazad
        </button>
        <h1>Vođeno skladištenje</h1>
      </div>

      <div className="putaway-item-info">
        <div className="item-field">
          <label>Šifra:</label>
          <span className="item-code">{item.artikal_sifra}</span>
        </div>
        <div className="item-field">
          <label>Naziv:</label>
          <span>{item.artikal_naziv}</span>
        </div>
        <div className="item-field">
          <label>Količina:</label>
          <span className="item-quantity">{item.kolicina_primljena} {item.jm}</span>
        </div>
      </div>

      {!showManualPicker && suggestions.length > 0 && (
        <div className="suggestions-section">
          <h2>🤖 AI Predlozi lokacija</h2>
          <div className="suggestions-list">
            {suggestions.map((suggestion, index) => (
              <div 
                key={suggestion.location_id}
                className={`suggestion-card ${selectedLocationId === suggestion.location_id ? 'selected' : ''}`}
                onClick={() => {
                  setSelectedLocationId(suggestion.location_id);
                  setSelectedLocationCode(suggestion.location_code);
                }}
              >
                <div className="suggestion-rank">#{index + 1}</div>
                <div className="suggestion-content">
                  <div className="suggestion-location">
                    <span className="location-code">{suggestion.location_code}</span>
                    <span className="location-naziv">{suggestion.location_naziv}</span>
                  </div>
                  <div className="suggestion-score">
                    Ocena: <strong>{suggestion.score.toFixed(0)}/100</strong>
                  </div>
                  <div className="suggestion-reason">{suggestion.reason}</div>
                  <div className="suggestion-capacity">
                    Popunjenost: {suggestion.occupancy_percentage.toFixed(0)}% | 
                    Dostupno: {parseFloat(suggestion.available_capacity.toString()).toFixed(2)} {item.jm}
                  </div>
                </div>
              </div>
            ))}
          </div>
          <button 
            className="manual-select-button"
            onClick={() => setShowManualPicker(true)}
          >
            📍 Izaberi ručno
          </button>
        </div>
      )}

      {showManualPicker && (
        <div className="manual-picker-section">
          <div className="manual-picker-header">
            <h2>Ručni izbor lokacije</h2>
            <button 
              className="back-to-suggestions"
              onClick={() => setShowManualPicker(false)}
            >
              ← Nazad na predloge
            </button>
          </div>
          <LocationPicker
            magacinId={localStorage.getItem('current_magacin_id') || ''}
            onSelect={(id, code) => {
              setSelectedLocationId(id);
              setSelectedLocationCode(code);
            }}
            selectedLocationId={selectedLocationId || undefined}
          />
        </div>
      )}

      {selectedLocationId && (
        <div className="putaway-footer">
          <div className="selected-location">
            <label>Izabrana lokacija:</label>
            <span className="location-code-large">{selectedLocationCode}</span>
          </div>
          <button 
            className="execute-button"
            onClick={handleExecutePutAway}
            disabled={executing}
          >
            {executing ? 'Skladišti se...' : '✅ Potvrdi skladištenje'}
          </button>
        </div>
      )}
    </div>
  );
};

