/**
 * CycleCountPage - Inventory cycle counting
 * Manhattan Active WMS - Popis magacina
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './CycleCountPage.css';

interface CycleCountItem {
  id: string;
  artikal_sifra: string;
  artikal_naziv: string;
  location_code: string;
  system_quantity: number;
  counted_quantity?: number;
  variance?: number;
  variance_percent?: number;
  is_discrepancy: boolean;
  requires_recount: boolean;
}

interface CycleCount {
  id: string;
  location_code?: string;
  location_naziv?: string;
  count_type?: string;
  scheduled_at: string;
  status: string;
  items: CycleCountItem[];
  accuracy_percentage: number;
}

export const CycleCountPage: React.FC = () => {
  const { countId } = useParams<{ countId: string }>();
  const navigate = useNavigate();
  
  const [cycleCount, setCycleCount] = useState<CycleCount | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentItemIndex, setCurrentItemIndex] = useState(0);
  const [countedQuantities, setCountedQuantities] = useState<Map<string, number>>(new Map());
  const [reasons, setReasons] = useState<Map<string, string>>(new Map());
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadCycleCount();
  }, [countId]);

  const loadCycleCount = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/locations/cycle-counts/${countId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setCycleCount(data);
        
        // Start if not started
        if (data.status === 'scheduled') {
          await startCycleCount();
        }
      }
    } catch (error) {
      console.error('Failed to load cycle count:', error);
    } finally {
      setLoading(false);
    }
  };

  const startCycleCount = async () => {
    try {
      await fetch(`/api/locations/cycle-counts/${countId}/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
    } catch (error) {
      console.error('Failed to start cycle count:', error);
    }
  };

  const handleCountItem = (itemId: string, quantity: number) => {
    const newCounted = new Map(countedQuantities);
    newCounted.set(itemId, quantity);
    setCountedQuantities(newCounted);
  };

  const handleReasonChange = (itemId: string, reason: string) => {
    const newReasons = new Map(reasons);
    newReasons.set(itemId, reason);
    setReasons(newReasons);
  };

  const handleNextItem = () => {
    if (currentItemIndex < (cycleCount?.items.length || 0) - 1) {
      setCurrentItemIndex(currentItemIndex + 1);
    }
  };

  const handlePreviousItem = () => {
    if (currentItemIndex > 0) {
      setCurrentItemIndex(currentItemIndex - 1);
    }
  };

  const handleCompleteCycleCount = async () => {
    if (!cycleCount) return;
    
    // Validate all items counted
    const uncounted = cycleCount.items.filter(item => !countedQuantities.has(item.id));
    if (uncounted.length > 0) {
      if (!confirm(`Ima ${uncounted.length} neprebrojanih stavki. Nastaviti?`)) {
        return;
      }
    }
    
    try {
      setSubmitting(true);
      const counts = cycleCount.items.map(item => ({
        item_id: item.id,
        counted_quantity: countedQuantities.get(item.id) || item.system_quantity,
        reason: reasons.get(item.id) || null
      }));
      
      const response = await fetch(`/api/locations/cycle-counts/${countId}/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ counts })
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`✅ Popis završen!\nTačnost: ${result.accuracy_percentage.toFixed(1)}%`);
        navigate('/cycle-counts');
      }
    } catch (error) {
      console.error('Failed to complete cycle count:', error);
      alert('❌ Greška pri završavanju popisa');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="cycle-count-loading">Učitavanje...</div>;
  }

  if (!cycleCount || cycleCount.items.length === 0) {
    return <div className="cycle-count-error">Nema stavki za popis</div>;
  }

  const currentItem = cycleCount.items[currentItemIndex];
  const countedQuantity = countedQuantities.get(currentItem.id);
  const variance = countedQuantity !== undefined ? countedQuantity - currentItem.system_quantity : 0;
  const variancePercent = currentItem.system_quantity > 0 ? (variance / currentItem.system_quantity) * 100 : 0;
  const progress = (countedQuantities.size / cycleCount.items.length) * 100;

  return (
    <div className="cycle-count-page">
      <div className="cycle-count-header">
        <button className="back-button" onClick={() => navigate(-1)}>
          ← Nazad
        </button>
        <h1>Popis magacina</h1>
      </div>

      <div className="count-progress">
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        </div>
        <div className="progress-text">
          {countedQuantities.size} / {cycleCount.items.length} prebrojano
        </div>
      </div>

      <div className="current-item-section">
        <div className="current-item-header">
          <h2>Stavka {currentItemIndex + 1}/{cycleCount.items.length}</h2>
          <span className="location-badge">{currentItem.location_code}</span>
        </div>

        <div className="current-item-card">
          <div className="item-info">
            <div className="item-field">
              <label>Šifra:</label>
              <span className="item-code">{currentItem.artikal_sifra}</span>
            </div>
            <div className="item-field">
              <label>Naziv:</label>
              <span>{currentItem.artikal_naziv}</span>
            </div>
            <div className="item-field">
              <label>Sistem:</label>
              <span className="system-quantity">{currentItem.system_quantity}</span>
            </div>
          </div>

          <div className="count-input-section">
            <label htmlFor="counted">Prebrojana količina:</label>
            <input
              id="counted"
              type="number"
              step="0.001"
              value={countedQuantity ?? ''}
              onChange={(e) => handleCountItem(currentItem.id, parseFloat(e.target.value) || 0)}
              placeholder="Unesite količinu"
              className="count-input"
            />
            <div className="quick-actions">
              <button
                className="quick-button"
                onClick={() => handleCountItem(currentItem.id, currentItem.system_quantity)}
              >
                = Sistem
              </button>
              <button
                className="quick-button"
                onClick={() => handleCountItem(currentItem.id, 0)}
              >
                0 (Nema)
              </button>
            </div>
          </div>

          {countedQuantity !== undefined && variance !== 0 && (
            <div className={`variance-section ${variance > 0 ? 'positive' : 'negative'}`}>
              <div className="variance-label">
                {variance > 0 ? '📈 Višak' : '📉 Manjak'}
              </div>
              <div className="variance-value">
                {variance > 0 ? '+' : ''}{variance} ({variancePercent > 0 ? '+' : ''}{variancePercent.toFixed(1)}%)
              </div>
              {Math.abs(variancePercent) > 5 && (
                <div className="variance-alert">⚠️ Odstupanje &gt; 5% - Potreban razlog</div>
              )}
              <textarea
                placeholder="Razlog odstupanja..."
                value={reasons.get(currentItem.id) || ''}
                onChange={(e) => handleReasonChange(currentItem.id, e.target.value)}
                className="reason-input"
                rows={2}
              />
            </div>
          )}

          <div className="item-navigation">
            <button
              className="nav-button"
              onClick={handlePreviousItem}
              disabled={currentItemIndex === 0}
            >
              ← Prethodna
            </button>
            {currentItemIndex < cycleCount.items.length - 1 ? (
              <button
                className="nav-button primary"
                onClick={handleNextItem}
                disabled={countedQuantity === undefined}
              >
                Sledeća →
              </button>
            ) : (
              <button
                className="nav-button complete"
                onClick={handleCompleteCycleCount}
                disabled={submitting}
              >
                {submitting ? 'Završavam...' : '✅ Završi popis'}
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="items-overview">
        <h3>Pregled stavki</h3>
        <div className="items-grid">
          {cycleCount.items.map((item, index) => {
            const counted = countedQuantities.get(item.id);
            const isCounted = counted !== undefined;
            const hasVariance = isCounted && counted !== item.system_quantity;
            
            return (
              <div
                key={item.id}
                className={`item-chip ${index === currentItemIndex ? 'current' : ''} ${isCounted ? 'counted' : ''} ${hasVariance ? 'variance' : ''}`}
                onClick={() => setCurrentItemIndex(index)}
              >
                <span className="chip-number">{index + 1}</span>
                {isCounted && <span className="chip-check">✓</span>}
                {hasVariance && <span className="chip-warning">!</span>}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

