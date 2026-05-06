import pandas as pd
import logging
from typing import List, Dict
from src.database.client import get_supabase_client

logger = logging.getLogger(__name__)

class CompetitorComparator:
    """Handles comparative analysis between multiple companies/products."""
    
    def __init__(self):
        self.supabase = get_supabase_client()

    def get_comparison_data(self, company_names: List[str]) -> Dict:
        """Fetches and aggregates data for a list of companies."""
        if not company_names:
            return {}

        results = {}
        for name in company_names:
            # 1. Get sentiment stats
            try:
                res = self.supabase.table('reviews').select('sentiment').eq('source', name).execute()
                df = pd.DataFrame(res.data)
                if not df.empty:
                    counts = df['sentiment'].value_counts(normalize=True).to_dict()
                else:
                    counts = {"positive": 0, "neutral": 0, "negative": 0}
            except Exception as e:
                logger.error(f"Error fetching sentiment for {name}: {e}")
                counts = {"positive": 0, "neutral": 0, "negative": 0}

            # 2. Get aspect scores
            try:
                res_aspects = self.supabase.table('aspects').select('*').eq('company_name', name).order('created_at', desc=True).limit(20).execute()
                aspects_df = pd.DataFrame(res_aspects.data)
                if not aspects_df.empty:
                    # Group by aspect and get latest/avg
                    latest_aspects = aspects_df.groupby('aspect')['score'].mean().to_dict()
                else:
                    latest_aspects = {}
            except Exception as e:
                logger.error(f"Error fetching aspects for {name}: {e}")
                latest_aspects = {}

            results[name] = {
                "sentiment": counts,
                "aspects": latest_aspects
            }
            
        return results
