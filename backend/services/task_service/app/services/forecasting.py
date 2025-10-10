import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import math
import statistics
from app_common.logging import get_logger

logger = get_logger(__name__)


class ForecastingEngine:
    """Simple linear regression + moving average forecasting engine."""
    
    def __init__(self):
        self.anomaly_threshold = 0.20  # 20% performance drop threshold
        self.confidence_level = 0.95  # 95% confidence interval
        self.min_data_points = 7  # Minimum data points for forecasting
    
    def generate_forecast(
        self,
        historical_data: List[Dict[str, Any]],
        horizon: int = 7,
        metric: str = "items_completed"
    ) -> Dict[str, Any]:
        """
        Generate forecast with confidence intervals and anomaly detection.
        
        Args:
            historical_data: List of historical data points
            horizon: Number of days to forecast
            metric: Metric name for forecasting
            
        Returns:
            Dictionary with forecast data, confidence intervals, and anomaly detection
        """
        if len(historical_data) < self.min_data_points:
            return self._create_empty_forecast(horizon, "Nedovoljno podataka za prognozu")
        
        try:
            # Extract values and dates
            values = [point.get("value", 0) for point in historical_data]
            dates = [point.get("date") for point in historical_data]
            
            # Detect anomalies in historical data
            anomalies = self._detect_anomalies(values)
            
            # Generate forecast using linear regression + moving average
            forecast_result = self._linear_regression_forecast(values, horizon)
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(
                values, forecast_result["forecast"], forecast_result["trend"]
            )
            
            # Generate future dates
            last_date = datetime.fromisoformat(dates[-1].replace('Z', '+00:00')) if dates[-1] else datetime.now()
            future_dates = [
                (last_date + timedelta(days=i+1)).isoformat()
                for i in range(horizon)
            ]
            
            # Create forecast data structure
            forecast_data = {
                "metric": metric,
                "horizon": horizon,
                "confidence": forecast_result["confidence"],
                "anomaly_detected": len(anomalies) > 0,
                "anomalies": anomalies,
                "trend": forecast_result["trend"],
                "seasonality": forecast_result.get("seasonality", 0),
                "actual": [
                    {
                        "date": date,
                        "value": value,
                        "is_anomaly": i in anomalies
                    }
                    for i, (date, value) in enumerate(zip(dates, values))
                ],
                "forecast": [
                    {
                        "date": future_dates[i],
                        "value": forecast_result["forecast"][i],
                        "lower_bound": confidence_intervals["lower"][i],
                        "upper_bound": confidence_intervals["upper"][i]
                    }
                    for i in range(horizon)
                ],
                "summary": {
                    "current_value": values[-1] if values else 0,
                    "forecast_avg": statistics.mean(forecast_result["forecast"]),
                    "trend_direction": "rastući" if forecast_result["trend"] > 0 else "opadajući" if forecast_result["trend"] < 0 else "stabilan",
                    "trend_strength": abs(forecast_result["trend"]),
                    "confidence_score": forecast_result["confidence"],
                    "anomaly_count": len(anomalies)
                }
            }
            
            return forecast_data
            
        except Exception as e:
            logger.error("FORECAST_GENERATION_ERROR", error=str(e), metric=metric)
            return self._create_empty_forecast(horizon, f"Greška pri generisanju prognoze: {str(e)}")
    
    def _linear_regression_forecast(self, values: List[float], horizon: int) -> Dict[str, Any]:
        """Generate forecast using linear regression with moving average smoothing."""
        n = len(values)
        x = np.arange(n)
        y = np.array(values)
        
        # Apply moving average smoothing (window=3)
        smoothed_values = self._moving_average(values, window=3)
        y_smooth = np.array(smoothed_values)
        
        # Linear regression: y = ax + b
        # Calculate slope (a) and intercept (b)
        x_mean = np.mean(x)
        y_mean = np.mean(y_smooth)
        
        numerator = np.sum((x - x_mean) * (y_smooth - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        
        if denominator == 0:
            # No trend, use last value
            slope = 0
            intercept = y_smooth[-1]
        else:
            slope = numerator / denominator
            intercept = y_mean - slope * x_mean
        
        # Generate forecast
        forecast = []
        for i in range(horizon):
            future_x = n + i
            predicted_value = slope * future_x + intercept
            # Ensure non-negative values
            forecast.append(max(0, predicted_value))
        
        # Calculate confidence based on R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((y_smooth - y_pred) ** 2)
        ss_tot = np.sum((y_smooth - y_mean) ** 2)
        
        if ss_tot == 0:
            r_squared = 1.0
        else:
            r_squared = 1 - (ss_res / ss_tot)
        
        confidence = max(0.1, min(0.95, r_squared))
        
        return {
            "forecast": forecast,
            "trend": slope,
            "confidence": confidence,
            "r_squared": r_squared
        }
    
    def _moving_average(self, values: List[float], window: int = 3) -> List[float]:
        """Apply moving average smoothing to reduce noise."""
        if len(values) < window:
            return values
        
        smoothed = []
        for i in range(len(values)):
            start = max(0, i - window + 1)
            end = i + 1
            window_values = values[start:end]
            smoothed.append(statistics.mean(window_values))
        
        return smoothed
    
    def _calculate_confidence_intervals(
        self, 
        historical_values: List[float], 
        forecast_values: List[float],
        trend: float
    ) -> Dict[str, List[float]]:
        """Calculate 95% confidence intervals for forecast."""
        # Calculate historical volatility
        if len(historical_values) < 2:
            volatility = 0.1  # Default 10% volatility
        else:
            returns = []
            for i in range(1, len(historical_values)):
                if historical_values[i-1] != 0:
                    ret = (historical_values[i] - historical_values[i-1]) / historical_values[i-1]
                    returns.append(ret)
            
            if returns:
                volatility = statistics.stdev(returns)
            else:
                volatility = 0.1
        
        # Calculate confidence intervals
        z_score = 1.96  # 95% confidence interval
        
        lower_bounds = []
        upper_bounds = []
        
        for i, forecast_value in enumerate(forecast_values):
            # Confidence interval widens with forecast horizon
            horizon_factor = 1 + (i * 0.1)  # 10% increase per day
            margin = forecast_value * volatility * z_score * horizon_factor
            
            lower_bounds.append(max(0, forecast_value - margin))
            upper_bounds.append(forecast_value + margin)
        
        return {
            "lower": lower_bounds,
            "upper": upper_bounds
        }
    
    def _detect_anomalies(self, values: List[float]) -> List[int]:
        """Detect anomalies using statistical methods."""
        if len(values) < 3:
            return []
        
        anomalies = []
        
        # Method 1: Z-score based anomaly detection
        mean_val = statistics.mean(values)
        stdev_val = statistics.stdev(values) if len(values) > 1 else 0
        
        if stdev_val > 0:
            for i, value in enumerate(values):
                z_score = abs((value - mean_val) / stdev_val)
                if z_score > 2.5:  # Threshold for anomaly
                    anomalies.append(i)
        
        # Method 2: Performance drop detection
        for i in range(1, len(values)):
            if values[i-1] > 0:
                drop_percentage = (values[i-1] - values[i]) / values[i-1]
                if drop_percentage > self.anomaly_threshold:
                    anomalies.append(i)
        
        # Remove duplicates and return
        return list(set(anomalies))
    
    def _create_empty_forecast(self, horizon: int, message: str) -> Dict[str, Any]:
        """Create empty forecast structure for error cases."""
        return {
            "metric": "unknown",
            "horizon": horizon,
            "confidence": 0.0,
            "anomaly_detected": False,
            "anomalies": [],
            "trend": 0.0,
            "seasonality": 0.0,
            "actual": [],
            "forecast": [],
            "summary": {
                "current_value": 0,
                "forecast_avg": 0,
                "trend_direction": "nepoznat",
                "trend_strength": 0,
                "confidence_score": 0,
                "anomaly_count": 0
            },
            "error": message
        }


# Global forecasting engine instance
forecasting_engine = ForecastingEngine()


def generate_kpi_forecast(
    historical_data: List[Dict[str, Any]],
    horizon: int = 7,
    metric: str = "items_completed"
) -> Dict[str, Any]:
    """Generate KPI forecast using the global forecasting engine."""
    return forecasting_engine.generate_forecast(historical_data, horizon, metric)
