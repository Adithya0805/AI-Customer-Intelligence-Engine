import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import time
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx

# Add root to sys.path to allow imports when running streamlit from anywhere
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from src.processing.pipeline import IntelligencePipeline
from config import settings

st.set_page_config(
    page_title="Customer Intelligence Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for aesthetics (glassmorphism & clean UI)
st.markdown("""
<style>
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 10px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-card h3 {
        color: #a0aec0;
        font-size: 1.1rem;
        margin-bottom: 5px;
    }
    .metric-card h2 {
        color: #fff;
        font-size: 2.5rem;
        margin: 0;
    }
    .alert-card-warning {
        background-color: rgba(255, 165, 0, 0.1);
        border-left: 5px solid orange;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
    }
    .alert-card-crisis {
        background-color: rgba(255, 0, 0, 0.1);
        border-left: 5px solid red;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
    }
    .model-card {
        background: linear-gradient(135deg, rgba(41, 128, 185, 0.1) 0%, rgba(142, 68, 173, 0.1) 100%);
        border: 1px solid rgba(142, 68, 173, 0.3);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .gradient-text {
        background: -webkit-linear-gradient(45deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_pipeline():
    return IntelligencePipeline()

@st.cache_data(ttl=10)
def load_data():
    data_path = settings.PROCESSED_DATA_DIR / "reviews.jsonl"
    if data_path.exists():
        df = pd.read_json(data_path, lines=True)
        df['date'] = pd.to_datetime(df['date'])
        return df
    return pd.DataFrame()

@st.cache_data(ttl=10)
def load_alerts():
    alerts_path = settings.ALERTS_DIR / "alerts.jsonl"
    if alerts_path.exists():
        df = pd.read_json(alerts_path, lines=True)
        # Keep latest alert per keyword
        if not df.empty:
            df = df.sort_values('timestamp').drop_duplicates('keyword', keep='last')
        return df
    return pd.DataFrame()

# Initialize session state variables for background thread
if 'pipeline_running' not in st.session_state:
    st.session_state.pipeline_running = False
if 'pipeline_messages' not in st.session_state:
    st.session_state.pipeline_messages = []
if 'pipeline_result' not in st.session_state:
    st.session_state.pipeline_result = None

pipeline = get_pipeline()

# --- Sidebar ---
st.sidebar.title("🧠 Intelligence Engine")
page = st.sidebar.radio("Navigation", ["📊 Dashboard", "⚡ Live Feed", "🗄️ Raw Data", "🧪 Analyze Studio"])

# --- Page: Dashboard ---
if page == "📊 Dashboard":
    col_title, col_refresh, col_reset = st.columns([2, 1, 1])
    with col_title:
        st.markdown('<h1 class="gradient-text">Customer Insights & Pressure Radar</h1>', unsafe_allow_html=True)
    with col_refresh:
        st.write("") # spacing
        if st.button("🔄 Refresh Data", use_container_width=True):
            load_data.clear()
            load_alerts.clear()
            st.rerun()
    with col_reset:
        st.write("") # spacing
        if st.button("🗑️ Reset All Data", type="primary", use_container_width=True):
            data_path = settings.PROCESSED_DATA_DIR / "reviews.jsonl"
            alerts_path = settings.ALERTS_DIR / "alerts.jsonl"
            if data_path.exists():
                data_path.unlink()
            if alerts_path.exists():
                alerts_path.unlink()
            load_data.clear()
            load_alerts.clear()
            st.rerun()
            
    df = load_data()
    alerts_df = load_alerts()
    
    if df.empty:
        st.info("No data available. Go to 'Live Feed' to ingest some reviews.")
    else:
        # High-level metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="metric-card"><h3>Total Reviews</h3><h2>{len(df)}</h2></div>', unsafe_allow_html=True)
        with col2:
            pos_pct = (df['sentiment'] == 'positive').mean() * 100
            st.markdown(f'<div class="metric-card"><h3>Positive Sentiment</h3><h2>{pos_pct:.1f}%</h2></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><h3>Active Alerts</h3><h2>{len(alerts_df)}</h2></div>', unsafe_allow_html=True)
            
        st.markdown("---")
        
        col_charts1, col_charts2 = st.columns([2, 1])
        
        with col_charts1:
            st.subheader("📈 Sentiment Trend")
            recent_df = df[df['date'] >= pd.Timestamp.now() - pd.Timedelta(days=30)].copy()
            if not recent_df.empty:
                # Decide grouping: if span is < 2 days, group by hour, else by day
                time_span = recent_df['date'].max() - recent_df['date'].min()
                if time_span < pd.Timedelta(days=2):
                    recent_df['grouped_time'] = recent_df['date'].dt.floor('h')
                else:
                    recent_df['grouped_time'] = recent_df['date'].dt.date
                
                daily_sentiment = recent_df.groupby(['grouped_time', 'sentiment']).size().reset_index(name='count')
                
                fig = px.line(daily_sentiment, x='grouped_time', y='count', color='sentiment', 
                              color_discrete_map={'positive': '#2ECC71', 'neutral': '#95A5A6', 'negative': '#E74C3C'},
                              markers=True)
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', 
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis_title="Time",
                    yaxis_title="Number of Reviews",
                    hovermode='x unified'
                )
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("Not enough recent data.")

        with col_charts2:
            st.subheader("🥧 Sentiment Distribution")
            fig2 = px.pie(df, names='sentiment', hole=0.5,
                          color='sentiment',
                          color_discrete_map={'positive': '#2ECC71', 'neutral': '#95A5A6', 'negative': '#E74C3C'})
            fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', showlegend=True, 
                               legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        
        # New Review Summary Table
        st.subheader("📝 Recent Reviews Preview")
        display_df = df.sort_values('date', ascending=False).head(10).copy()
        
        # Display as styled dataframe
        def sentiment_badge(val):
            if val == 'positive': return "🟩 Positive"
            elif val == 'negative': return "🟥 Negative"
            return "⬜ Neutral"
            
        display_df['Sentiment'] = display_df['sentiment'].apply(sentiment_badge)
        display_df['Preview'] = display_df['clean_text'].str[:100] + "..."
        display_df['Score'] = display_df['sentiment_score'].round(3)
        display_df['Date'] = display_df['date'].dt.strftime('%Y-%m-%d %H:%M')
        
        st.dataframe(
            display_df[['Date', 'Sentiment', 'Score', 'Preview', 'source']],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.subheader("⚠️ Pressure Radar (Emerging Issues)")
        
        if alerts_df.empty:
            st.success("✅ No emerging issues detected! Pressure is normal.")
        else:
            for _, alert in alerts_df.iterrows():
                css_class = "alert-card-crisis" if alert['status'] == 'EMERGING_CRISIS' else "alert-card-warning"
                icon = "🔥" if alert['status'] == 'EMERGING_CRISIS' else "⚠️"
                
                st.markdown(f"""
                <div class="{css_class}">
                    <h4 style="margin-top:0;">{icon} {alert['keyword'].title()}</h4>
                    <p style="margin-bottom:5px;"><b>Pressure Score:</b> {alert['pressure_score']}x surge compared to baseline.</p>
                    <small>Recent Importance: {alert['recent_importance']:.3f} | Baseline: {alert['baseline_importance']:.3f}</small>
                </div>
                """, unsafe_allow_html=True)


# --- Page: Live Feed ---
elif page == "⚡ Live Feed":
    st.markdown('<h1 class="gradient-text">Live Ingestion Feed</h1>', unsafe_allow_html=True)
    st.write("Extract, clean, and analyze reviews in real-time.")
    
    if "target_url" not in st.session_state:
        st.session_state.target_url = ""
    
    target_url = st.text_input("Enter URL to scrape reviews:", key="target_url", placeholder="https://example.com/product/reviews", disabled=st.session_state.pipeline_running)
    
    def run_pipeline_thread(url):
        def progress_cb(msg):
            st.session_state.pipeline_messages.append(msg)
            
        try:
            result = pipeline.run(url, progress_callback=progress_cb)
            st.session_state.pipeline_result = result
        except Exception as e:
            st.session_state.pipeline_result = {"status": "error", "message": str(e)}
        finally:
            st.session_state.pipeline_running = False

    if st.button("🚀 Run Intelligence Pipeline", disabled=st.session_state.pipeline_running, type="primary"):
        if target_url:
            # Clear old state
            st.session_state.pipeline_messages = []
            st.session_state.pipeline_result = None
            st.session_state.pipeline_running = True
            
            # Start background thread
            thread = threading.Thread(target=run_pipeline_thread, args=(target_url,))
            add_script_run_ctx(thread) # Important for Streamlit threading state propagation
            thread.start()
            st.rerun()
        else:
            st.warning("Please enter a URL.")

    if st.session_state.pipeline_running:
        with st.status("🧠 Running Intelligence Engine... (You can safely navigate away)", expanded=True) as status:
            # Show the last 5 messages
            for msg in st.session_state.pipeline_messages[-5:]:
                st.write(f"⚙️ {msg}")
            
            st.write("...") # indicator it's still going
        time.sleep(1) # Poll every second
        st.rerun()
    elif st.session_state.pipeline_result:
        res = st.session_state.pipeline_result
        if res['status'] == 'success':
            st.success(f"✅ Successfully Processed {res['processed_count']} reviews.")
            if res.get('alerts_generated', 0) > 0:
                st.warning(f"⚠️ Generated {res['alerts_generated']} new pressure alerts.")
            if st.button("Clear Result"):
                st.session_state.pipeline_result = None
                st.session_state.pipeline_messages = []
                st.rerun()
        else:
            st.error(f"❌ Pipeline failed: {res.get('message')}")
            if st.button("Clear Error"):
                st.session_state.pipeline_result = None
                st.session_state.pipeline_messages = []
                st.rerun()

# --- Page: Raw Data ---
elif page == "🗄️ Raw Data":
    st.markdown('<h1 class="gradient-text">Processed Data Explorer</h1>', unsafe_allow_html=True)
    
    # Model Intelligence Card
    st.markdown("""
    <div class="model-card">
        <h3 style="margin-top:0;">🤖 Intelligence Model Specs</h3>
        <p style="margin-bottom:5px;"><b>Architecture:</b> RoBERTa (Robustly Optimized BERT Pretraining Approach)</p>
        <p style="margin-bottom:5px;"><b>Loaded Weights:</b> <code>cardiffnlp/twitter-roberta-base-sentiment-latest</code></p>
        <p style="margin-bottom:0;"><b>Device:</b> Auto-detected CPU/GPU | <b>Task:</b> Multi-class Sentiment Classification</p>
    </div>
    """, unsafe_allow_html=True)
    
    df = load_data()
    
    if not df.empty:
        # Data Quality Metrics
        st.subheader("📊 Data Quality Metrics")
        q_col1, q_col2, q_col3 = st.columns(3)
        with q_col1:
            st.metric("Total Records", len(df))
        with q_col2:
            st.metric("Clean Text Present", f"{(df['clean_text'].str.len() > 0).mean()*100:.1f}%")
        with q_col3:
            st.metric("Ratings Captured", f"{(~df['rating'].isna()).mean()*100:.1f}%")
        
        st.markdown("---")
        
        # Filters
        st.subheader("🔍 Explore Data")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            sentiment_filter = st.multiselect("Filter by Sentiment", options=['positive', 'neutral', 'negative'], default=['positive', 'neutral', 'negative'])
        with col_f2:
            search_query = st.text_input("Search in text...")
            
        filtered_df = df[df['sentiment'].isin(sentiment_filter)]
        if search_query:
            filtered_df = filtered_df[filtered_df['clean_text'].str.contains(search_query, case=False, na=False)]
            
        # Display Styled Table
        st.dataframe(
            filtered_df[['date', 'source', 'sentiment', 'sentiment_score', 'clean_text', 'rating', 'url']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "sentiment_score": st.column_config.NumberColumn("Score", format="%.3f"),
                "date": st.column_config.DatetimeColumn("Date", format="YYYY-MM-DD HH:mm"),
                "url": st.column_config.LinkColumn("URL"),
                "sentiment": st.column_config.TextColumn("Sentiment")
            }
        )
        
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            st.download_button(
                label="📥 Download CSV",
                data=filtered_df.to_csv(index=False).encode('utf-8'),
                file_name='customer_intelligence_data.csv',
                mime='text/csv',
                use_container_width=True
            )
    else:
        st.info("No data available.")

# --- Page: Analyze Studio ---
elif page == "🧪 Analyze Studio":
    st.markdown('<h1 class="gradient-text">Analyze Studio</h1>', unsafe_allow_html=True)
    st.write("Upload or paste data to instantly analyze sentiment and auto-discover topics.")

    tab1, tab2, tab3 = st.tabs(["📋 Paste Text", "📁 Upload CSV", "📄 Upload TXT"])
    
    input_data = None
    input_type = None
    csv_col = None

    with tab1:
        pasted_text = st.text_area("Paste reviews (one per line)", height=200, disabled=st.session_state.pipeline_running)
        if pasted_text:
            input_data = pasted_text
            input_type = "text"
            st.caption(f"Detected ~{len([l for l in pasted_text.splitlines() if len(l.strip())>5])} reviews")
            
    with tab2:
        uploaded_csv = st.file_uploader("Upload CSV file", type=['csv'], disabled=st.session_state.pipeline_running)
        if uploaded_csv:
            df_upload = pd.read_csv(uploaded_csv)
            st.dataframe(df_upload.head(3))
            csv_col = st.selectbox("Select the column containing review text:", df_upload.columns)
            input_data = df_upload
            input_type = "csv"

    with tab3:
        uploaded_txt = st.file_uploader("Upload TXT file", type=['txt'], disabled=st.session_state.pipeline_running)
        if uploaded_txt:
            input_data = uploaded_txt.getvalue().decode("utf-8")
            input_type = "text"
            st.caption(f"Detected ~{len([l for l in input_data.splitlines() if len(l.strip())>5])} reviews")

    def run_studio_thread(data, type_, col=None):
        def progress_cb(msg):
            st.session_state.pipeline_messages.append(msg)
            
        try:
            if type_ == "text":
                result = pipeline.run_from_text(data, progress_callback=progress_cb)
            elif type_ == "csv":
                result = pipeline.run_from_dataframe(data, col, progress_callback=progress_cb)
            st.session_state.pipeline_result = result
        except Exception as e:
            st.session_state.pipeline_result = {"status": "error", "message": str(e)}
        finally:
            st.session_state.pipeline_running = False

    st.markdown("---")
    if st.button("🚀 Analyze Now", disabled=st.session_state.pipeline_running, type="primary"):
        if input_data is not None:
            st.session_state.pipeline_messages = []
            st.session_state.pipeline_result = None
            st.session_state.pipeline_running = True
            
            thread = threading.Thread(target=run_studio_thread, args=(input_data, input_type, csv_col))
            add_script_run_ctx(thread)
            thread.start()
            st.rerun()
        else:
            st.warning("Please provide input data first.")

    if st.session_state.pipeline_running:
        with st.status("🧠 Analyzing data... (You can safely navigate away)", expanded=True) as status:
            for msg in st.session_state.pipeline_messages[-5:]:
                st.write(f"⚙️ {msg}")
        time.sleep(1)
        st.rerun()
    elif st.session_state.pipeline_result:
        res = st.session_state.pipeline_result
        if res['status'] == 'success':
            st.success(f"✅ Analysis Complete: Processed {res['processed_count']} reviews.")
            
            # --- Results Panel ---
            proc_df = pd.DataFrame(res['processed_data'])
            
            st.markdown("### 📊 Summary Dashboard")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Reviews", len(proc_df))
            with col2:
                st.metric("Avg Score", f"{proc_df['sentiment_score'].mean():.2f}")
            with col3:
                dom_sent = proc_df['sentiment'].mode()[0] if not proc_df.empty else "N/A"
                emoji = "😊" if dom_sent == "positive" else "😐" if dom_sent == "neutral" else "😡"
                st.metric("Dominant Sentiment", f"{emoji} {dom_sent.title()}")

            st.markdown("### 📈 Sentiment Breakdown")
            sent_counts = proc_df['sentiment'].value_counts().reset_index()
            sent_counts.columns = ['sentiment', 'count']
            sent_counts['percent'] = (sent_counts['count'] / len(proc_df)) * 100
            
            fig_bar = px.bar(sent_counts, y='sentiment', x='percent', color='sentiment',
                            color_discrete_map={'positive': '#2ECC71', 'neutral': '#95A5A6', 'negative': '#E74C3C'},
                            orientation='h', text=sent_counts['percent'].apply(lambda x: f'{x:.1f}%'))
            fig_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', showlegend=False, xaxis_title="Percentage (%)", yaxis_title="")
            st.plotly_chart(fig_bar, use_container_width=True)

            st.markdown("### 🏷️ Topic Clusters Discovered")
            clusters = res.get('clusters', {})
            for c_id, c_info in clusters.items():
                with st.expander(f"Cluster: {c_info['label']} ({len(c_info['indices'])} reviews)"):
                    cluster_indices = c_info['indices']
                    examples = proc_df.iloc[cluster_indices]
                    st.dataframe(examples[['sentiment', 'topic_cluster', 'clean_text']], use_container_width=True, hide_index=True)

            st.markdown("### 💾 Export Results")
            dl_col1, dl_col2, dl_col3 = st.columns(3)
            with dl_col1:
                st.download_button("📥 Download CSV", proc_df.to_csv(index=False).encode('utf-8'), "analysis_result.csv", "text/csv", use_container_width=True)
            with dl_col2:
                # Add Excel download since we installed openpyxl
                import io
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    proc_df.to_excel(writer, index=False)
                st.download_button("📄 Download Excel", buffer.getvalue(), "analysis_result.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            with dl_col3:
                summary_text = f"Analyzed {len(proc_df)} reviews. Dominant sentiment: {dom_sent.title()}. Top topics: {', '.join([c['label'] for c in clusters.values()])}."
                st.text_area("Summary", summary_text, height=68, disabled=True)
                
            if st.button("Clear Results"):
                st.session_state.pipeline_result = None
                st.session_state.pipeline_messages = []
                st.rerun()
                
        else:
            st.error(f"❌ Pipeline failed: {res.get('message')}")
            if st.button("Clear Error"):
                st.session_state.pipeline_result = None
                st.session_state.pipeline_messages = []
                st.rerun()
