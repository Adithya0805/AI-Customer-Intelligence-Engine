import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import time
import threading
from datetime import datetime, timedelta
from streamlit.runtime.scriptrunner import add_script_run_ctx

# Add root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from src.processing.pipeline import IntelligencePipeline
from config import settings

# --- UI Configuration ---
st.set_page_config(
    page_title="AI Customer Intel Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_custom_css():
    st.markdown("""
    <style>
        /* Main gradient background */
        .stApp {
            background: radial-gradient(circle at top right, #1a1a2e, #0f0f1a);
        }
        
        /* Glassmorphism containers */
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(12px);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            margin-bottom: 20px;
        }
        
        /* Metric styling */
        .metric-label {
            color: #8a8fb1;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        .metric-value {
            color: #ffffff;
            font-size: 2.2rem;
            font-weight: 700;
        }
        .metric-trend {
            font-size: 0.85rem;
            margin-top: 5px;
        }
        
        /* Gradient text */
        .gradient-text {
            background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }
        
        /* Alert cards */
        .alert-pulse {
            border-left: 4px solid #ff4b4b;
            background: rgba(255, 75, 75, 0.05);
            padding: 15px;
            border-radius: 0 10px 10px 0;
            margin-bottom: 10px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.2); }
            70% { box-shadow: 0 0 0 10px rgba(255, 75, 75, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 75, 75, 0); }
        }
    </style>
    """, unsafe_allow_html=True)

# --- Logic & Data ---
@st.cache_resource
def get_pipeline():
    """Initializes the pipeline once and caches it."""
    return IntelligencePipeline()

def startup_check():
    """Splash screen/check for first run."""
    if 'startup_done' not in st.session_state:
        with st.empty():
            for i in range(101):
                st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 80vh;">
                    <h1 class="gradient-text" style="font-size: 3rem;">🧠 AI Customer Intel</h1>
                    <p style="color: #8a8fb1;">Booting production engine...</p>
                    <div style="width: 300px; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px;">
                        <div style="width: {i}%; height: 100%; background: linear-gradient(90deg, #ff6b6b, #4ecdc4); border-radius: 2px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.01)
            st.session_state.startup_done = True
            st.rerun()

@st.cache_data(ttl=30)
def load_production_data():
    try:
        from src.database.client import get_supabase_client
        supabase = get_supabase_client()
        res = supabase.table('reviews').select('*').order('date', desc=True).limit(2000).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df['date'] = pd.to_datetime(df['date'])
            return df
    except Exception as e:
        st.sidebar.error(f"DB Error: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=30)
def load_alerts_data():
    try:
        from src.database.client import get_supabase_client
        supabase = get_supabase_client()
        res = supabase.table('alerts').select('*').order('timestamp', desc=True).limit(50).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df.drop_duplicates('keyword', keep='first')
    except Exception as e:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=60)
def load_latest_summary():
    try:
        from src.database.client import get_supabase_client
        supabase = get_supabase_client()
        res = supabase.table('summaries').select('*').order('created_at', desc=True).limit(1).execute()
        if res.data:
            return res.data[0]
    except Exception:
        pass
    return None

def render_word_cloud(df):
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    
    # Filter for negative reviews to see what the pain points are
    neg_text = " ".join(df[df['sentiment'] == 'negative']['clean_text'].astype(str))
    if not neg_text.strip():
        st.write("Not enough negative feedback for word cloud.")
        return

    wc = WordCloud(width=800, height=400, background_color=None, mode="RGBA", 
                   colormap="Reds", max_words=50).generate(neg_text)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    fig.patch.set_alpha(0) # Transparent background
    st.pyplot(fig)

# --- Component Helpers ---
def render_metric(label, value, trend=None, trend_up=True):
    trend_html = ""
    if trend:
        color = "#4ecdc4" if trend_up else "#ff6b6b"
        icon = "↑" if trend_up else "↓"
        trend_html = f'<div class="metric-trend" style="color: {color};">{icon} {trend}</div>'
    
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {trend_html}
    </div>
    """, unsafe_allow_html=True)

def render_sentiment_bar(df):
    counts = df['sentiment'].value_counts()
    pos = counts.get('positive', 0)
    neu = counts.get('neutral', 0)
    neg = counts.get('negative', 0)
    total = pos + neu + neg
    
    if total == 0: return
    
    p_pos, p_neu, p_neg = pos/total*100, neu/total*100, neg/total*100
    
    st.markdown(f"""
    <div style="height: 24px; width: 100%; display: flex; border-radius: 12px; overflow: hidden; margin: 10px 0;">
        <div style="width: {p_pos}%; background: #2ecc71; transition: width 0.5s;"></div>
        <div style="width: {p_neu}%; background: #95a5a6; transition: width 0.5s;"></div>
        <div style="width: {p_neg}%; background: #e74c3c; transition: width 0.5s;"></div>
    </div>
    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #8a8fb1;">
        <span>Pos: {p_pos:.0f}%</span>
        <span>Neu: {p_neu:.0f}%</span>
        <span>Neg: {p_neg:.0f}%</span>
    </div>
    """, unsafe_allow_html=True)

# --- Sidebar ---
def render_sidebar():
    st.sidebar.markdown('<h1 class="gradient-text" style="font-size: 1.5rem;">AI Intel Engine</h1>', unsafe_allow_html=True)
    st.sidebar.caption("Production MVP v1.0")
    
    nav = st.sidebar.radio("Navigation", ["📈 Dashboard", "🏆 Competitor Intel", "🧠 Analyze Studio", "⚡ Live Monitor", "📋 Watchlist", "⚙️ Settings"])
    
    st.sidebar.markdown("---")
    # Health Indicators
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.markdown('<div style="font-size: 0.7rem; color: #8a8fb1;">DATABASE</div>', unsafe_allow_html=True)
        st.success("CONNECTED")
    with col2:
        st.markdown('<div style="font-size: 0.7rem; color: #8a8fb1;">AI MODEL</div>', unsafe_allow_html=True)
        st.info("LOADED")
        
    st.sidebar.markdown("---")
    user = get_current_user()
    if user:
        st.sidebar.markdown(f"👤 **{user.email}**")
        if st.sidebar.button("🔓 Logout", use_container_width=True):
            logout()
            
    if st.sidebar.button("🗑️ Reset Cache", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    return nav

def render_auth_page():
    st.markdown('<div style="display: flex; justify-content: center; margin-top: 50px;">', unsafe_allow_html=True)
    st.markdown('<h1 class="gradient-text" style="font-size: 3rem;">🧠 AI Customer Intel</h1>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login", use_container_width=True):
                    res = login(email, password)
                    if res['status'] == 'success':
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(f"Login failed: {res['message']}")
        
        with tab2:
            st.info("Join the enterprise intelligence platform.")
            with st.form("signup_form"):
                new_email = st.text_input("Email")
                new_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Create Account", use_container_width=True):
                    if new_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        res = signup(new_email, new_password)
                        if res['status'] == 'success':
                            st.success("Account created! Please check your email for verification (if enabled) and login.")
                        else:
                            st.error(f"Signup failed: {res['message']}")

from src.auth.supabase_auth import is_authenticated, login, signup, logout, get_current_user

# --- Main App ---
def main():
    inject_custom_css()
    
    # --- Authentication Gate ---
    if not is_authenticated():
        render_auth_page()
        return

    startup_check()
    nav = render_sidebar()
    
    # Start background scheduler for watchlist
    from src.automation.scheduler import start_scheduler
    start_scheduler()
    
    pipeline = get_pipeline()
    
    if nav == "📈 Dashboard":
        st.markdown('<h2 class="gradient-text">Executive Intelligence Dashboard</h2>', unsafe_allow_html=True)
        
        df = load_production_data()
        alerts_df = load_alerts_data()
        summary_export = load_latest_summary()
        
        if df.empty:
            st.info("No data found. Start by scraping a URL in 'Live Monitor' or pasting text in 'Analyze Studio'.")
            return

        # Anomaly Detection (Phase 4)
        from src.intelligence.anomaly_detector import AnomalyDetector
        detector = AnomalyDetector()
        anomalies = detector.detect_anomalies(df)
        
        if anomalies:
            for anomaly in anomalies:
                st.warning(f"🚨 **{anomaly['type']}**: {anomaly['description']}")

        # Export Row
        col_exp1, col_exp2 = st.columns([5, 1])
        with col_exp2:
            if summary_export:
                from src.reporting.pdf_generator import generate_pdf_report
                sent_counts = df['sentiment'].value_counts().to_dict()
                aspects_meta = summary_export['metadata'].get('aspects', []) if summary_export.get('metadata') else []
                alerts_meta = alerts_df.to_dict('records') if not alerts_df.empty else []
                
                pdf_bytes = generate_pdf_report(
                    "All Sources", 
                    summary_export['content'], 
                    sent_counts, 
                    aspects_meta, 
                    alerts_meta
                )
                st.download_button(
                    label="📥 Export PDF",
                    data=pdf_bytes,
                    file_name=f"Executive_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

        # Filters ... (existing filters)
        with st.expander("🔍 Dashboard Filters"):
            col1, col2, col3 = st.columns(3)
            with col1:
                date_range = st.selectbox("Time Horizon", ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"], index=1)
            with col2:
                source_filter = st.multiselect("Source Filter", options=df['source'].unique(), default=df['source'].unique())
            with col3:
                st.write("") # Spacer
                if st.button("Apply Filters", use_container_width=True):
                    st.rerun()

        # Metrics ... (existing metrics)
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            render_metric("Total Reviews", f"{len(df):,}")
        with m2:
            pos_pct = (df['sentiment'] == 'positive').mean() * 100
            render_metric("Avg Sentiment", f"{pos_pct:.1f}%", "Positive", True)
        with m3:
            neg_count = (df['sentiment'] == 'negative').sum()
            render_metric("Total Risks", neg_count, f"{neg_count/len(df)*100:.1f}% Share", False)
        with m4:
            render_metric("Active Alerts", len(alerts_df))

        st.markdown("---")
        
        # Charts Row
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("📈 Sentiment Trends & Forecast")
            # Resample by day
            df_trend = df.copy()
            df_trend['day'] = df_trend['date'].dt.date
            trend_data = df_trend.groupby(['day', 'sentiment']).size().reset_index(name='count')
            
            fig = px.line(trend_data, x='day', y='count', color='sentiment', 
                         color_discrete_map={'positive': '#2ecc71', 'neutral': '#95a5a6', 'negative': '#e74c3c'},
                         template="plotly_dark", height=400)
            
            # Phase 4: Forecasting
            if st.checkbox("🔮 Show 7-Day Forecast"):
                from src.intelligence.forecaster import SentimentForecaster
                forecaster = SentimentForecaster()
                f_res = forecaster.forecast_sentiment(df)
                if f_res['status'] == 'success':
                    # Add positive forecast
                    fig.add_scatter(x=f_res['dates'], y=f_res['pos_forecast'], name='Positive (Forecast)', 
                                   line=dict(color='#2ecc71', dash='dash'))
                    # Add negative forecast
                    fig.add_scatter(x=f_res['dates'], y=f_res['neg_forecast'], name='Negative (Forecast)', 
                                   line=dict(color='#e74c3c', dash='dash'))

            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            st.subheader("🎯 Share of Voice")
            render_sentiment_bar(df)
            fig_pie = px.pie(df, names='sentiment', hole=0.6,
                            color='sentiment',
                            color_discrete_map={'positive': '#2ecc71', 'neutral': '#95a5a6', 'negative': '#e74c3c'},
                            template="plotly_dark", height=300)
            fig_pie.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")
        
        # Pressure & Summaries ... (existing s1, s2)
        s1, s2 = st.columns([1, 1])
        with s1:
            st.subheader("🔥 Pressure Radar (Emerging Issues)")
            if alerts_df.empty:
                st.success("No critical issues building up in the last 7 days.")
            else:
                for _, row in alerts_df.iterrows():
                    st.markdown(f"""
                    <div class="alert-pulse">
                        <div style="font-weight: 700; color: #ff4b4b;">{row['keyword'].upper()} SURGE</div>
                        <div style="font-size: 0.8rem; color: #8a8fb1;">Pressure Score: {row['pressure_score']}x normal baseline</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.subheader("🌋 Pain Point Word Cloud")
            render_word_cloud(df)
                    
        with s2:
            st.subheader("🤖 AI Executive Summary")
            if summary_export:
                st.markdown(summary_export['content'])
                st.caption(f"Generated at: {summary_export['created_at']}")
            else:
                st.info("No AI summary available yet. Run an analysis in 'Live Monitor' to generate one.")

        st.markdown("---")
        st.subheader("📋 Recent Reviews")
        st.dataframe(df[['date', 'source', 'sentiment', 'original_text']].head(20), use_container_width=True)

    elif nav == "🏆 Competitor Intel":
        # ... (Competitor Intel logic remains same)
        st.markdown('<h2 class="gradient-text">Competitor Intelligence</h2>', unsafe_allow_html=True)
        
        from src.database.client import get_supabase_client
        supabase = get_supabase_client()
        res_watch = supabase.table('watchlist').select('company_name').execute()
        companies_list = [r['company_name'] for r in res_watch.data] if res_watch.data else []
        
        if not companies_list:
            st.warning("Add companies to your Watchlist first to compare them.")
        else:
            selected_comp = st.multiselect("Select Companies to Compare:", options=companies_list, default=companies_list[:2] if len(companies_list) >= 2 else companies_list)
            
            if st.button("Run Comparison Analysis", type="primary"):
                from src.intelligence.comparator import CompetitorComparator
                comp_analyzer = CompetitorComparator()
                comp_results = comp_analyzer.get_comparison_data(selected_comp)
                
                if comp_results:
                    c_col1, c_col2 = st.columns(2)
                    for idx, (c_name, c_data) in enumerate(comp_results.items()):
                        target_col = c_col1 if idx % 2 == 0 else c_col2
                        with target_col:
                            st.markdown(f"""
                            <div class="glass-card">
                                <h3 style="margin-top:0;">{c_name}</h3>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            c_sent = c_data['sentiment']
                            st.write("**Sentiment Profile:**")
                            st.write(f"Positive: {c_sent.get('positive', 0)*100:.1f}%")
                            st.progress(c_sent.get('positive', 0))
                            
                            if c_data['aspects']:
                                st.write("**Top Aspects:**")
                                for asp, sc in c_data['aspects'].items():
                                    st.caption(f"{asp}: {sc:.2f}")
                else:
                    st.info("No data found for selected companies. Ensure they have been synced in Watchlist.")

    elif nav == "🧠 Analyze Studio":
        # ... (Analyze Studio logic remains same)
        st.markdown('<h2 class="gradient-text">AI Analytics Studio</h2>', unsafe_allow_html=True)
        st.write("Perform deep-dive analysis on custom datasets.")
        
        tab1, tab2 = st.tabs(["📄 Paste Reviews", "📊 Upload Dataset"])
        
        with tab1:
            text_input = st.text_area("Paste one review per line:", height=200, placeholder="Product is amazing but shipping was slow...")
            if st.button("Run AI Analysis", type="primary"):
                if text_input:
                    with st.status("Initializing AI Pipeline...", expanded=True) as status:
                        res = pipeline.run_from_text(text_input, progress_callback=lambda m: status.write(f"⚙️ {m}"), user_id=st.session_state.user.id)
                        if res['status'] == 'success':
                            status.update(label="Analysis Complete!", state="complete")
                            st.markdown("### 📋 Executive Summary")
                            st.markdown(res['executive_summary'])
                            
                            st.markdown("### 📊 Distribution")
                            render_sentiment_bar(pd.DataFrame(res['processed_data']))
                            
                            with st.expander("View Processed Data"):
                                st.dataframe(res['processed_data'], use_container_width=True)
                        else:
                            st.error(res['message'])
                else:
                    st.warning("Please enter some text.")

        with tab2:
            uploaded_file = st.file_uploader("Upload CSV or Excel file", type=['csv', 'xlsx'])
            if uploaded_file:
                df_upload = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                st.dataframe(df_upload.head(), use_container_width=True)
                
                text_col = st.selectbox("Select the column containing reviews:", df_upload.columns)
                
                if st.button("Analyze Uploaded Data", type="primary"):
                    with st.status("Analyzing Dataset...", expanded=True) as status:
                        res = pipeline.run_from_dataframe(df_upload, text_col, progress_callback=lambda m: status.write(f"⚙️ {m}"), user_id=st.session_state.user.id)
                        if res['status'] == 'success':
                            status.update(label="Analysis Complete!", state="complete")
                            st.markdown("### 📋 Executive Summary")
                            st.markdown(res['executive_summary'])
                            
                            st.markdown("### 📊 Distribution")
                            render_sentiment_bar(pd.DataFrame(res['processed_data']))
                        else:
                            st.error(res['message'])

    elif nav == "⚡ Live Monitor":
        st.markdown('<h2 class="gradient-text">Live Intelligence Feed</h2>', unsafe_allow_html=True)
        url = st.text_input("Enter Product URL to Monitor:", placeholder="https://www.trustpilot.com/review/example.com")
        
        if st.button("🚀 Start Extraction", type="primary"):
            if url:
                with st.status("Processing Live Feed...", expanded=True) as status:
                    res = pipeline.run(url, progress_callback=lambda m: status.write(f"⚙️ {m}"), user_id=st.session_state.user.id)
                    if res['status'] == 'success':
                        status.update(label=f"Successfully extracted {res['processed_count']} reviews", state="complete")
                        st.balloons()
                    else:
                        st.error(res['message'])
            else:
                st.warning("Enter a valid URL.")

    elif nav == "📋 Watchlist":
        st.markdown('<h2 class="gradient-text">Watchlist Management</h2>', unsafe_allow_html=True)
        st.caption("Auto-monitored assets in the background.")
        
        from src.database.client import get_supabase_client, get_service_client
        supabase = get_supabase_client()
        service_supabase = get_service_client()

        # Add to Watchlist
        with st.expander("➕ Add New URL to Watchlist"):
            with st.form("add_watchlist_form"):
                new_url = st.text_input("URL")
                company = st.text_input("Company Name")
                if st.form_submit_button("Add to Watchlist"):
                    if new_url:
                        try:
                            service_supabase.table('watchlist').insert({
                                "url": new_url, 
                                "company_name": company,
                                "user_id": st.session_state.user.id
                            }).execute()
                            st.success(f"Added {company} to watchlist!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding to watchlist: {e}")
                    else:
                        st.warning("URL is required.")

        # Display Watchlist
        try:
            res = supabase.table('watchlist').select('*').execute()
            if res.data:
                watchlist_df = pd.DataFrame(res.data)
                
                from src.automation.scheduler import get_scheduler_status
                sched_status = get_scheduler_status()
                st.info(f"🤖 **Auto-Sync Status:** {sched_status['status'].upper()} | **Next Run:** {sched_status['next_run']}")

                for _, item in watchlist_df.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div class="glass-card" style="padding: 15px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h4 style="margin: 0;">{item['company_name']}</h4>
                                    <code style="font-size: 0.7rem;">{item['url']}</code>
                                    <div style="font-size: 0.7rem; color: #8a8fb1; margin-top: 5px;">
                                        Last Scraped: {item['last_scraped_at'] if item['last_scraped_at'] else 'Never'}
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"Sync {item['company_name']}", key=f"sync_{item['id']}"):
                                with st.status(f"Syncing {item['company_name']}..."):
                                    pipeline.run(item['url'], user_id=st.session_state.user.id)
                                    st.success("Done!")
                                    st.rerun()
                        with col2:
                            if st.button(f"Remove", key=f"del_{item['id']}"):
                                service_supabase.table('watchlist').delete().eq('id', item['id']).execute()
                                st.rerun()
            else:
                st.info("Watchlist is empty.")
        except Exception as e:
            st.error(f"Error loading watchlist: {e}")

    elif nav == "⚙️ Settings":
        st.markdown('<h2 class="gradient-text">System Settings</h2>', unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["🔑 API Keys", "🔌 Webhooks", "⚙️ Preferences"])
        
        from src.database.client import get_service_client
        from src.auth.audit import log_action
        service_supabase = get_service_client()

        with tab1:
            st.subheader("External API Access")
            st.write("Use these keys to integrate with external tools.")
            
            with st.form("generate_key_form"):
                key_name = st.text_input("Key Name (e.g. 'Production BI')")
                if st.form_submit_button("Generate New API Key"):
                    import secrets
                    import hashlib
                    new_key = secrets.token_urlsafe(32)
                    key_hash = hashlib.sha256(new_key.encode()).hexdigest()
                    service_supabase.table('api_keys').insert({
                        "user_id": st.session_state.user.id,
                        "key_hash": key_hash,
                        "name": key_name
                    }).execute()
                    
                    log_action(st.session_state.user.id, "API_KEY_CREATED", metadata={"name": key_name})
                    st.success("API Key Generated Successfully!")
                    st.code(new_key)
                    st.warning("Copy this key now. It will not be shown again for security reasons.")
            
            st.markdown("---")
            st.subheader("Your API Keys")
            res_keys = service_supabase.table('api_keys').select('*').eq('user_id', st.session_state.user.id).execute()
            if res_keys.data:
                for k in res_keys.data:
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"**{k['name']}** (Created: {k['created_at'][:10]})")
                    if c2.button("Revoke", key=f"rev_{k['id']}"):
                        service_supabase.table('api_keys').delete().eq('id', k['id']).execute()
                        log_action(st.session_state.user.id, "API_KEY_REVOKED", k['id'])
                        st.rerun()
            else:
                st.info("No API keys found.")

        with tab2:
            st.subheader("Outbound Webhooks")
            st.write("Push events to your servers in real-time.")
            
            with st.form("register_webhook_form"):
                wh_url = st.text_input("Webhook URL")
                if st.form_submit_button("Register Webhook"):
                    import secrets
                    service_supabase.table('webhooks').insert({
                        "user_id": st.session_state.user.id,
                        "url": wh_url,
                        "secret": secrets.token_urlsafe(32)
                    }).execute()
                    log_action(st.session_state.user.id, "WEBHOOK_REGISTERED", metadata={"url": wh_url})
                    st.success("Webhook registered!")
                    st.rerun()

        with tab3:
            st.subheader("General Configuration")
            st.write(f"**Environment:** `{settings.ENVIRONMENT}`")
            
            # Phase 5: Shared Reports Management
            st.markdown("---")
            st.subheader("🔗 Active Public Portals")
            res_shares = service_supabase.table('shared_reports').select('*').eq('user_id', st.session_state.user.id).execute()
            if res_shares.data:
                for s in res_shares.data:
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"Portal for **{s['company_name']}**")
                    if c2.button("Revoke Link", key=f"rev_share_{s['id']}"):
                        service_supabase.table('shared_reports').delete().eq('id', s['id']).execute()
                        log_action(st.session_state.user.id, "SHARE_REVOKED", s['id'])
                        st.rerun()
            else:
                st.info("No active public portals.")

            st.markdown("---")
            if st.button("🗑️ Wipe My Data", type="primary"):
                st.error("This will delete all your reviews and alerts. This action is irreversible.")
                if st.button("CONFIRM WIPE"):
                    service_supabase.table('reviews').delete().eq('user_id', st.session_state.user.id).execute()
                    log_action(st.session_state.user.id, "DATA_WIPE")
                    st.success("Data wiped.")

    # Shared Report Button on Dashboard
    if nav == "📈 Dashboard" and not df.empty:
        st.markdown("---")
        if st.button("🔗 Generate Public Insight Portal", use_container_width=True):
            import secrets
            token = secrets.token_urlsafe(16)
            try:
                service_supabase.table('shared_reports').insert({
                    "user_id": st.session_state.user.id,
                    "token": token,
                    "company_name": "Global Dashboard"
                }).execute()
                log_action(st.session_state.user.id, "SHARE_CREATED")
                share_url = f"https://your-app.com/public?token={token}" # Placeholder
                st.success("Public Portal Generated!")
                st.code(share_url)
            except Exception as e:
                st.error(f"Sharing failed: {e}")

if __name__ == "__main__":
    main()
