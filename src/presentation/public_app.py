import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from src.database.client import get_service_client
from config import settings

# Page Config for Public Portal
st.set_page_config(
    page_title="Insight Portal | AI Customer Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling (Minimalist for Public View)
st.markdown("""
    <style>
    .report-header {
        padding: 2rem;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    # 1. Extract Token from URL
    # st.query_params is the modern way in Streamlit
    token = st.query_params.get("token")
    
    if not token:
        st.error("Invalid or missing share token.")
        st.stop()

    # 2. Validate Token & Get Config
    supabase = get_service_client()
    res_share = supabase.table('shared_reports').select('*').eq('token', token).execute()
    
    if not res_share.data:
        st.error("This report link has expired or is invalid.")
        st.stop()
        
    share = res_share.data[0]
    company = share['company_name']
    user_id = share['user_id'] # The owner
    
    st.markdown(f"""
    <div class="report-header">
        <h1>{company} Intelligence Portal</h1>
        <p>Curated Business Insights & Sentiment Analysis</p>
    </div>
    """, unsafe_allow_html=True)

    # 3. Load Data scoped to company (using owner's user_id via service role)
    # Note: We use service role here because the public user isn't logged in.
    # The 'shared_reports' table acts as our authorization gate.
    res_reviews = supabase.table('reviews').select('*').eq('user_id', user_id).order('date', desc=True).limit(500).execute()
    df = pd.DataFrame(res_reviews.data)
    
    if df.empty:
        st.info("No data available for this report yet.")
        return

    # 4. Render Portal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Sentiment Performance")
        df_trend = df.copy()
        df_trend['day'] = pd.to_datetime(df_trend['date']).dt.date
        trend_data = df_trend.groupby(['day', 'sentiment']).size().reset_index(name='count')
        fig = px.line(trend_data, x='day', y='count', color='sentiment', 
                     color_discrete_map={'positive': '#2ecc71', 'neutral': '#95a5a6', 'negative': '#e74c3c'},
                     template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🎯 Distribution")
        fig_pie = px.pie(df, names='sentiment', hole=0.6,
                        color='sentiment',
                        color_discrete_map={'positive': '#2ecc71', 'neutral': '#95a5a6', 'negative': '#e74c3c'},
                        template="plotly_dark", height=350)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    
    # AI Summary
    res_sum = supabase.table('summaries').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(1).execute()
    if res_sum.data:
        st.subheader("🤖 AI Executive Summary")
        st.markdown(f'<div class="glass-card">{res_sum.data[0]["content"]}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📋 Recent Feedback")
    st.dataframe(df[['date', 'sentiment', 'original_text']].head(50), use_container_width=True)

    st.caption(f"Generated via AI Customer Intelligence Engine | Report Owner ID: {user_id[:8]}...")

if __name__ == "__main__":
    main()
