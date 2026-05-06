import pandas as pd
import numpy as np
import logging
from typing import Dict, Any
from statsmodels.tsa.holtwinters import ExponentialSmoothing

logger = logging.getLogger(__name__)

class SentimentForecaster:
    """
    Lightweight time-series forecasting for sentiment trends.
    Uses Holt-Winters Exponential Smoothing (statsmodels).
    """
    
    def forecast_sentiment(self, df: pd.DataFrame, horizon: int = 7) -> Dict[str, Any]:
        """
        Forecasts positive and negative review volume for the next N days.
        """
        if df.empty or len(df) < 14:
            return {"status": "error", "message": "Not enough historical data for forecasting (min 14 days)."}

        try:
            df['date'] = pd.to_datetime(df['date'])
            # Resample to daily frequency
            daily_pos = df[df['sentiment'] == 'positive'].set_index('date').resample('D').size()
            daily_neg = df[df['sentiment'] == 'negative'].set_index('date').resample('D').size()

            # Ensure complete index
            full_range = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='D')
            daily_pos = daily_pos.reindex(full_range, fill_value=0)
            daily_neg = daily_neg.reindex(full_range, fill_value=0)

            results = {"dates": [], "pos_forecast": [], "neg_forecast": []}
            
            # Forecast Positive
            if daily_pos.sum() > 0:
                model_pos = ExponentialSmoothing(daily_pos, seasonal='add', seasonal_periods=7).fit()
                pred_pos = model_pos.forecast(horizon)
                results["pos_forecast"] = pred_pos.clip(lower=0).tolist()
            
            # Forecast Negative
            if daily_neg.sum() > 0:
                model_neg = ExponentialSmoothing(daily_neg, seasonal='add', seasonal_periods=7).fit()
                pred_neg = model_neg.forecast(horizon)
                results["neg_forecast"] = pred_neg.clip(lower=0).tolist()

            # Generate future dates
            future_dates = pd.date_range(start=full_range[-1] + pd.Timedelta(days=1), periods=horizon, freq='D')
            results["dates"] = future_dates.strftime('%Y-%m-%d').tolist()
            results["status"] = "success"
            
            return results
        except Exception as e:
            logger.error(f"Forecasting failed: {e}")
            return {"status": "error", "message": str(e)}
