/**
 * PickingRoutePage - Optimized picking route display
 * Manhattan Active WMS - Tvoja ruta (Vođeno izdavanje)
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './PickingRoutePage.css';

interface PickTask {
  stavka_id: string;
  artikal_sifra: string;
  artikal_naziv: string;
  location_id: string;
  location_code: string;
  location_full_path: string;
  quantity: number;
  sequence: number;
}

interface PickRoute {
  zaduznica_id: string;
  route_id: string;
  tasks: PickTask[];
  total_distance_meters?: number;
  estimated_time_minutes?: number;
  created_at: string;
}

export const PickingRoutePage: React.FC = () => {
  const { zaduznicaId } = useParams<{ zaduznicaId: string }>();
  const navigate = useNavigate();
  
  const [route, setRoute] = useState<PickRoute | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentTaskIndex, setCurrentTaskIndex] = useState(0);
  const [completedTasks, setCompletedTasks] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadOrGenerateRoute();
  }, [zaduznicaId]);

  const loadOrGenerateRoute = async () => {
    try {
      setLoading(true);
      // Try to load existing route
      let response = await fetch(`/api/locations/pick-routes/${zaduznicaId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok && response.status === 404) {
        // Generate new route
        response = await fetch('/api/locations/pick-routes', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            zaduznica_id: zaduznicaId,
            algorithm: 'nearest_neighbor'
          })
        });
      }
      
      if (response.ok) {
        const data = await response.json();
        setRoute(data);
      }
    } catch (error) {
      console.error('Failed to load picking route:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteTask = (taskId: string) => {
    const newCompleted = new Set(completedTasks);
    newCompleted.add(taskId);
    setCompletedTasks(newCompleted);
    
    // Auto-advance to next task
    if (currentTaskIndex < (route?.tasks.length || 0) - 1) {
      setCurrentTaskIndex(currentTaskIndex + 1);
    }
  };

  const handleJumpToTask = (index: number) => {
    setCurrentTaskIndex(index);
  };

  if (loading) {
    return <div className="picking-route-loading">Optimizujem rutu...</div>;
  }

  if (!route || route.tasks.length === 0) {
    return <div className="picking-route-error">Nema stavki za izdavanje</div>;
  }

  const currentTask = route.tasks[currentTaskIndex];
  const progress = (completedTasks.size / route.tasks.length) * 100;

  return (
    <div className="picking-route-page">
      <div className="picking-route-header">
        <button className="back-button" onClick={() => navigate(-1)}>
          ← Nazad
        </button>
        <h1>Tvoja ruta</h1>
      </div>

      <div className="route-progress">
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        </div>
        <div className="progress-text">
          {completedTasks.size} / {route.tasks.length} završeno
        </div>
      </div>

      {route.estimated_time_minutes && (
        <div className="route-stats">
          <div className="stat">
            <span className="stat-icon">⏱️</span>
            <span className="stat-value">{route.estimated_time_minutes} min</span>
            <span className="stat-label">Procenjeno vreme</span>
          </div>
          {route.total_distance_meters && (
            <div className="stat">
              <span className="stat-icon">📏</span>
              <span className="stat-value">{route.total_distance_meters.toFixed(0)} m</span>
              <span className="stat-label">Ukupna distanca</span>
            </div>
          )}
        </div>
      )}

      <div className="current-task-section">
        <div className="current-task-header">
          <h2>Trenutna lokacija</h2>
          <span className="task-sequence">#{currentTask.sequence}</span>
        </div>
        <div className="current-task-card">
          <div className="task-location">
            <span className="location-code-huge">{currentTask.location_code}</span>
            <span className="location-path">{currentTask.location_full_path}</span>
          </div>
          <div className="task-article">
            <div className="article-code">{currentTask.artikal_sifra}</div>
            <div className="article-naziv">{currentTask.artikal_naziv}</div>
            <div className="article-quantity">
              Izdaj: <strong>{currentTask.quantity}</strong>
            </div>
          </div>
          {!completedTasks.has(currentTask.stavka_id) && (
            <button
              className="complete-task-button"
              onClick={() => handleCompleteTask(currentTask.stavka_id)}
            >
              ✅ Završi stavku
            </button>
          )}
          {completedTasks.has(currentTask.stavka_id) && (
            <div className="task-completed-badge">✓ Završeno</div>
          )}
        </div>
      </div>

      <div className="remaining-tasks-section">
        <h3>Preostale lokacije</h3>
        <div className="tasks-list">
          {route.tasks.map((task, index) => (
            <div
              key={task.stavka_id}
              className={`task-item ${index === currentTaskIndex ? 'current' : ''} ${
                completedTasks.has(task.stavka_id) ? 'completed' : ''
              }`}
              onClick={() => handleJumpToTask(index)}
            >
              <div className="task-sequence-badge">#{task.sequence}</div>
              <div className="task-content">
                <div className="task-location-code">{task.location_code}</div>
                <div className="task-article-code">{task.artikal_sifra}</div>
                <div className="task-quantity">x{task.quantity}</div>
              </div>
              {completedTasks.has(task.stavka_id) && (
                <span className="task-check">✓</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

