import os
import google.generativeai as genai
from typing import List, Dict, Any
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class LLMSummarizer:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Use gemini-1.5-flash for fast, high-quality summaries
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    def generate_executive_summary(self, reviews: List[Dict], clusters: List[Dict], alerts: List[Dict]) -> str:
        """Generates an executive summary based on the analyzed data."""
        if not self.model:
            return "⚠️ Gemini API key not found. Please add GEMINI_API_KEY to your .env file to enable AI summaries."

        if not reviews:
            return "No data available to summarize."

        try:
            total_reviews = len(reviews)
            positive_count = sum(1 for r in reviews if r.get('sentiment') == 'positive')
            negative_count = sum(1 for r in reviews if r.get('sentiment') == 'negative')
            
            cluster_details = []
            for cluster in clusters:
                label = cluster['label']
                count = cluster['count']
                cluster_details.append(f"- {label}: {count} reviews")
            
            alert_details = []
            for alert in alerts:
                if alert['status'] == 'CRITICAL' or alert['status'] == 'WARNING':
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
            
            Format the output nicely using Markdown. Do not include generic introductory phrases like "Here is the summary".
            """

            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(f"Error generating summary with Gemini: {e}")
            return f"⚠️ Failed to generate AI summary. Ensure your Gemini API key is valid. Error: {str(e)}"
