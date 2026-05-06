import os
import google.generativeai as genai
from typing import List, Dict, Any
from dotenv import load_dotenv
import logging
from config import settings

logger = logging.getLogger(__name__)

class LLMSummarizer:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                self.model = None
        else:
            self.model = None

    def _generate_fallback_summary(self, reviews: List[Dict], clusters: Dict, alerts: List[Dict]) -> str:
        """Generates a non-AI statistical summary."""
        total = len(reviews)
        pos = sum(1 for r in reviews if r.get('sentiment') == 'positive')
        neg = sum(1 for r in reviews if r.get('sentiment') == 'negative')
        
        summary = f"### 📊 Quick Insights (Statistical)\n\n"
        summary += f"Analyzed **{total}** reviews with an overall sentiment of **{pos/total*100:.1f}% positive** and **{neg/total*100:.1f}% negative**.\n\n"
        
        if clusters:
            summary += "**Key Topics Discovered:**\n"
            for c in clusters.values():
                summary += f"- {c['label']} ({len(c['indices'])} reviews)\n"
        
        if alerts:
            summary += "\n**⚠️ Emerging Issues:**\n"
            for a in alerts[:3]:
                summary += f"- Potential issue with **'{a['keyword']}'** (Pressure: {a['pressure_score']}x)\n"
                
        return summary

    def generate_executive_summary(self, reviews: List[Dict], clusters: Dict, alerts: List[Dict]) -> str:
        """Generates an executive summary based on the analyzed data."""
        if not self.model:
            return self._generate_fallback_summary(reviews, clusters, alerts) + \
                   "\n\n> [!NOTE]\n> *Add a GEMINI_API_KEY to your .env for a detailed AI executive brief.*"

        if not reviews:
            return "No data available to summarize."

        try:
            total_reviews = len(reviews)
            positive_count = sum(1 for r in reviews if r.get('sentiment') == 'positive')
            negative_count = sum(1 for r in reviews if r.get('sentiment') == 'negative')
            
            cluster_details = []
            for cluster in clusters.values():
                label = cluster['label']
                count = len(cluster['indices'])
                cluster_details.append(f"- {label}: {count} reviews")
            
            alert_details = []
            for alert in alerts:
                # PressureDetector uses 'EMERGING_CRISIS' and 'WARNING'
                if alert['status'] in ['EMERGING_CRISIS', 'WARNING']:
                    alert_details.append(f"{alert['status']} ALERT: '{alert['keyword']}' (Pressure Score: {alert['pressure_score']:.2f})")

            prompt = f"""
            You are an expert Customer Intelligence Analyst. 
            Write a concise, professional Executive Brief (2-3 paragraphs) summarizing the following customer feedback data.
            Focus on actionable insights. Highlight any critical alerts or major negative trends that need immediate attention.
            
            DATA SUMMARY:
            Total Reviews Analyzed: {total_reviews}
            Positive: {positive_count}
            Negative: {negative_count}
            
            MAIN TOPIC CLUSTERS:
            {chr(10).join(cluster_details)}
            
            EMERGING ISSUES/ALERTS:
            {chr(10).join(alert_details) if alert_details else "None detected in this batch."}
            
            Format the output nicely using Markdown with clear headers. Do not include introductory phrases.
            """

            # Limit prompt size for Gemini
            safe_prompt = prompt[:30000] 
            
            response = self.model.generate_content(safe_prompt)
            summary_text = response.text
            
            # Persist to database
            self._save_summary_to_db(summary_text, total_reviews, positive_count, negative_count)
            
            return summary_text

        except Exception as e:
            logger.error(f"Error generating summary with Gemini: {e}")
            return self._generate_fallback_summary(reviews, clusters, alerts)

    def _save_summary_to_db(self, content: str, total: int, pos: int, neg: int):
        """Persists the generated summary to the database."""
        try:
            from src.database.client import get_service_client
            supabase = get_service_client()
            
            data = {
                "content": content,
                "source_context": "pipeline_run",
                "metadata": {
                    "total_reviews": total,
                    "positive": pos,
                    "negative": neg
                }
            }
            supabase.table('summaries').insert(data).execute()
        except Exception as e:
            logger.error(f"Failed to save summary to DB: {e}")
