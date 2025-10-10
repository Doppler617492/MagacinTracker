# Predictive Analytics Documentation

## Overview

The Predictive Analytics system provides AI-powered forecasting and anomaly detection for warehouse KPIs. Using linear regression and moving average algorithms, the system predicts future trends, detects performance anomalies, and provides confidence intervals for decision-making.

## Features

### 🔮 Forecasting Engine
- **Linear Regression**: Trend-based predictions with moving average smoothing
- **Confidence Intervals**: 95% confidence bounds for forecast accuracy
- **Multi-horizon Support**: 1-30 day forecast periods
- **Seasonality Detection**: Weekly patterns and cyclical behavior
- **Real-time Updates**: Automatic forecast refresh every 5 minutes

### ⚠️ Anomaly Detection
- **Performance Drop Detection**: Identifies >20% performance decreases
- **Statistical Anomalies**: Z-score based outlier detection
- **Real-time Alerts**: Immediate notifications for detected anomalies
- **Historical Analysis**: Tracks anomaly patterns over time

### 📊 Visualization
- **Forecast Overlay**: Transparent forecast lines on existing charts
- **Confidence Bands**: Visual confidence intervals
- **Anomaly Highlighting**: Marked anomalous data points
- **Trend Indicators**: Visual trend direction and strength

## Technical Architecture

### Backend Implementation

#### Forecasting Engine (`ForecastingEngine`)

**Core Algorithm**:
```python
# Linear Regression: y = ax + b
slope = Σ((x - x̄)(y - ȳ)) / Σ((x - x̄)²)
intercept = ȳ - slope * x̄

# Moving Average Smoothing (window=3)
smoothed[i] = mean(values[i-2:i+1])

# Confidence Interval (95%)
margin = forecast_value * volatility * 1.96 * horizon_factor
```

**Key Components**:
- **Data Preprocessing**: Moving average smoothing to reduce noise
- **Trend Analysis**: Linear regression for trend detection
- **Confidence Calculation**: R-squared based confidence scoring
- **Anomaly Detection**: Z-score and performance drop analysis

#### API Endpoints

##### GET /api/kpi/predict
Generate KPI forecast with confidence intervals and anomaly detection.

**Parameters**:
- `metric` (string): Metric to forecast (default: "items_completed")
- `period` (int): Historical period in days (7-365, default: 90)
- `horizon` (int): Forecast horizon in days (1-30, default: 7)
- `radnja_id` (UUID, optional): Filter by store
- `radnik_id` (UUID, optional): Filter by worker

**Response**:
```json
{
  "metric": "items_completed",
  "horizon": 7,
  "confidence": 0.85,
  "anomaly_detected": true,
  "anomalies": [15, 23, 45],
  "trend": 2.3,
  "seasonality": 0.1,
  "actual": [
    {
      "date": "2024-01-15T00:00:00Z",
      "value": 150,
      "is_anomaly": false
    }
  ],
  "forecast": [
    {
      "date": "2024-01-22T00:00:00Z",
      "value": 165,
      "lower_bound": 145,
      "upper_bound": 185
    }
  ],
  "summary": {
    "current_value": 150,
    "forecast_avg": 165,
    "trend_direction": "rastući",
    "trend_strength": 2.3,
    "confidence_score": 0.85,
    "anomaly_count": 3
  },
  "generated_at": "2024-01-15T10:30:00Z",
  "processing_time_ms": 245
}
```

### Frontend Implementation

#### Admin Analytics Integration

**Forecast Toggle**:
- **Button**: "🔮 Prikaži prognozu" with loading states
- **Chart Overlay**: Forecast line with confidence bands
- **Anomaly Warning**: Red-bordered warning card for detected anomalies
- **KPI Enhancement**: Forecast values in KPI cards

**Chart Configuration**:
```typescript
const lineConfig = {
  data: combinedData, // actual + forecast
  xField: 'date',
  yField: 'value',
  seriesField: 'type',
  color: (type) => {
    switch (type) {
      case 'actual': return '#1890ff';
      case 'forecast': return '#722ed1';
    }
  },
  area: {
    style: {
      fill: 'l(270) 0:#722ed1 1:#722ed1',
      fillOpacity: 0.1
    }
  }
};
```

#### TV Dashboard Integration

**Anomaly Overlay**:
- **Fixed Position**: Top-center overlay for critical alerts
- **Animated Entry**: Smooth slide-down animation
- **Auto-dismiss**: Configurable display duration
- **Gradient Background**: Eye-catching red gradient

**Forecast Indicators**:
- **KPI Enhancement**: Forecast values in metric cards
- **Trend Display**: Trend direction in metric labels
- **Real-time Updates**: 5-minute refresh intervals

## Forecasting Models

### Linear Regression Model

**Mathematical Foundation**:
```
y = ax + b

where:
- y = predicted value
- x = time index
- a = slope (trend)
- b = intercept

Confidence = R² = 1 - (SS_res / SS_tot)
```

**Advantages**:
- **Simplicity**: Easy to understand and implement
- **Speed**: Fast computation (<300ms)
- **Stability**: Consistent results across datasets
- **Interpretability**: Clear trend direction and strength

**Limitations**:
- **Linear Assumption**: Assumes linear trends
- **No External Factors**: Doesn't consider external variables
- **Limited Seasonality**: Basic seasonal pattern detection

### Moving Average Smoothing

**Algorithm**:
```python
def moving_average(values, window=3):
    smoothed = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        end = i + 1
        window_values = values[start:end]
        smoothed.append(mean(window_values))
    return smoothed
```

**Benefits**:
- **Noise Reduction**: Eliminates random fluctuations
- **Trend Preservation**: Maintains underlying trends
- **Stability**: Reduces forecast volatility
- **Adaptability**: Adjusts to changing patterns

### Anomaly Detection

#### Z-Score Method
```python
z_score = abs((value - mean) / std_dev)
if z_score > 2.5:  # Threshold
    anomaly_detected = True
```

#### Performance Drop Detection
```python
drop_percentage = (previous_value - current_value) / previous_value
if drop_percentage > 0.20:  # 20% threshold
    anomaly_detected = True
```

## Performance Metrics

### Forecasting Accuracy

**Metrics**:
- **MAPE** (Mean Absolute Percentage Error): <15% target
- **RMSE** (Root Mean Square Error): Minimized for trend accuracy
- **Confidence Score**: R² based, 0.7-0.95 typical range
- **Processing Time**: <300ms for 90-day history

**Benchmarks**:
- **Short-term (1-7 days)**: 85-95% accuracy
- **Medium-term (8-14 days)**: 75-85% accuracy
- **Long-term (15-30 days)**: 65-75% accuracy

### Anomaly Detection

**Metrics**:
- **Precision**: True positives / (True positives + False positives)
- **Recall**: True positives / (True positives + False negatives)
- **F1-Score**: Harmonic mean of precision and recall

**Targets**:
- **Precision**: >80% (minimize false alarms)
- **Recall**: >70% (catch most anomalies)
- **F1-Score**: >75% (balanced performance)

## Configuration

### Environment Variables

```env
# Forecasting Configuration
FORECAST_CACHE_TTL=86400  # 24 hours
FORECAST_MIN_DATA_POINTS=7
FORECAST_ANOMALY_THRESHOLD=0.20  # 20%
FORECAST_CONFIDENCE_LEVEL=0.95   # 95%

# Performance Tuning
FORECAST_MAX_HORIZON=30
FORECAST_MAX_PERIOD=365
FORECAST_PROCESSING_TIMEOUT=5000  # 5 seconds
```

### Model Parameters

```python
class ForecastingConfig:
    anomaly_threshold = 0.20      # 20% performance drop
    confidence_level = 0.95       # 95% confidence interval
    min_data_points = 7           # Minimum for forecasting
    moving_average_window = 3     # Smoothing window
    z_score_threshold = 2.5       # Anomaly detection
```

## Audit & Monitoring

### Audit Events

#### Forecast Generation
```json
{
  "event": "FORECAST_GENERATED",
  "metric": "items_completed",
  "period": 90,
  "horizon": 7,
  "processing_time_ms": 245,
  "confidence": 0.85,
  "anomaly_detected": true,
  "user_id": "uuid"
}
```

#### Anomaly Detection
```json
{
  "event": "ANOMALY_DETECTED",
  "metric": "items_completed",
  "anomaly_count": 3,
  "anomaly_indices": [15, 23, 45],
  "severity": "medium",
  "user_id": "uuid"
}
```

### Prometheus Metrics

```python
# Forecast Performance
forecast_latency_ms = Histogram('forecast_processing_duration_seconds')
forecast_confidence_avg = Gauge('forecast_confidence_average')
forecast_anomaly_total = Counter('forecast_anomalies_detected_total')

# Model Accuracy
forecast_accuracy_mape = Gauge('forecast_accuracy_mape')
forecast_accuracy_rmse = Gauge('forecast_accuracy_rmse')
```

## Usage Examples

### Basic Forecast Request

```bash
curl -X GET "http://localhost:8123/api/kpi/predict" \
  -H "Authorization: Bearer <token>" \
  -G \
  -d "metric=items_completed" \
  -d "period=90" \
  -d "horizon=7"
```

### Filtered Forecast

```bash
curl -X GET "http://localhost:8123/api/kpi/predict" \
  -H "Authorization: Bearer <token>" \
  -G \
  -d "metric=completion_time" \
  -d "period=30" \
  -d "horizon=14" \
  -d "radnja_id=uuid"
```

### Frontend Integration

```typescript
// Enable forecast in Admin Analytics
const { data: forecastData } = useQuery({
  queryKey: ['forecast', filters],
  queryFn: () => getKPIForecast({
    metric: 'items_completed',
    period: 90,
    horizon: 7
  }),
  enabled: showForecast
});

// Display anomaly warning
{forecastData?.anomaly_detected && (
  <Alert
    message="⚠️ Anomalija detektovana"
    description={`${forecastData.anomaly_count} anomalija u poslednjih ${forecastData.parameters.period} dana`}
    type="warning"
  />
)}
```

## Troubleshooting

### Common Issues

#### 1. Low Forecast Confidence
**Symptoms**: Confidence score <0.7
**Solutions**:
- Increase historical data period
- Check for data quality issues
- Verify trend stability
- Consider seasonal adjustments

#### 2. False Anomaly Alerts
**Symptoms**: Too many anomaly detections
**Solutions**:
- Adjust anomaly threshold (increase from 0.20)
- Review Z-score threshold (increase from 2.5)
- Check for data outliers
- Validate data collection process

#### 3. Forecast Inaccuracy
**Symptoms**: High MAPE/RMSE values
**Solutions**:
- Increase moving average window
- Check for external factors
- Validate historical data
- Consider model retraining

#### 4. Performance Issues
**Symptoms**: Slow forecast generation
**Solutions**:
- Reduce historical period
- Optimize data queries
- Enable caching
- Check database performance

### Debug Mode

Enable detailed logging:
```env
LOG_LEVEL=DEBUG
FORECAST_DEBUG=true
```

This will log:
- Model parameters and calculations
- Anomaly detection details
- Performance metrics
- Data preprocessing steps

## Future Enhancements

### Planned Features

#### 1. Advanced Models
- **ARIMA**: Autoregressive Integrated Moving Average
- **Prophet**: Facebook's forecasting library
- **LSTM**: Long Short-Term Memory networks
- **Ensemble Methods**: Multiple model combination

#### 2. External Factors
- **Weather Integration**: Weather impact on performance
- **Holiday Calendar**: Holiday effect modeling
- **Market Conditions**: Economic indicator integration
- **Seasonal Patterns**: Advanced seasonality detection

#### 3. Real-time Features
- **Streaming Forecasts**: Real-time model updates
- **Adaptive Thresholds**: Dynamic anomaly detection
- **Online Learning**: Continuous model improvement
- **A/B Testing**: Model performance comparison

#### 4. Visualization Enhancements
- **Interactive Charts**: Drill-down capabilities
- **3D Visualizations**: Multi-dimensional forecasts
- **Animation**: Smooth forecast transitions
- **Export Options**: PDF/PNG forecast reports

### Technical Improvements

#### 1. Performance Optimization
- **GPU Acceleration**: CUDA-based computations
- **Distributed Computing**: Multi-node processing
- **Caching Strategy**: Intelligent forecast caching
- **Batch Processing**: Bulk forecast generation

#### 2. Model Management
- **Model Versioning**: Track model iterations
- **A/B Testing**: Compare model performance
- **Auto-retraining**: Automatic model updates
- **Model Monitoring**: Performance degradation detection

#### 3. Integration Features
- **API Gateway**: Centralized forecast access
- **Webhook Support**: Real-time forecast notifications
- **Mobile SDK**: Mobile app integration
- **Third-party APIs**: External system integration

## Support & Maintenance

### Monitoring

**Key Metrics**:
- Forecast accuracy trends
- Anomaly detection rates
- Processing time performance
- User engagement with forecasts

**Alerts**:
- Forecast accuracy degradation
- High anomaly detection rates
- Processing time spikes
- Model performance issues

### Maintenance Tasks

**Regular Tasks**:
- Model performance review (weekly)
- Anomaly threshold tuning (monthly)
- Historical data cleanup (quarterly)
- Model retraining (quarterly)

**Optimization**:
- Parameter tuning based on performance
- Data quality improvements
- Algorithm enhancements
- Infrastructure scaling

### Support Contacts

- **Technical Issues**: development@magacin.com
- **Model Questions**: data-science@magacin.com
- **Performance Issues**: ops@magacin.com
- **Feature Requests**: product@magacin.com

---

**Documentation Version**: 1.0  
**Last Updated**: January 15, 2024  
**Maintained by**: Data Science Team
