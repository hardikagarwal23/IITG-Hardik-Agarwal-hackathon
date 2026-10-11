import json
import os
import sys
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.feed_processor import FeedProcessor
from src.pipeline import RiskLensPipeline

st.set_page_config(
    page_title="Signal2Stress | Risk Intelligence",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_resource
def get_pipeline():
    return RiskLensPipeline()

@st.cache_resource
def get_processor():
    return FeedProcessor()

pipeline = get_pipeline()
feed_processor = get_processor()

# Custom Styling
st.markdown(
    """
    <style>
    .metric-card { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 1rem; border-radius: 0.5rem; margin-bottom: 0.5rem; }
    .status-badge { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.85rem; font-weight: 600; }
    .badge-direct { background-color: #ffebee; color: #c62828; }
    .badge-sector { background-color: #fff3e0; color: #ef6c00; }
    .badge-macro { background-color: #e8f5e9; color: #2e7d32; }
    .badge-none { background-color: #f5f5f5; color: #616161; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.title("Signal2Stress")
st.caption("News-to-Portfolio Risk Intelligence | Wholesale Portfolio Stress Engine")

# Sidebar Controls
st.sidebar.header("Run Settings")
mode = st.sidebar.radio(
    "Workflow Mode",
    ["Interactive Analysis", "Preset Scenarios", "Live Feed Stream"],
)

st.sidebar.divider()
st.sidebar.subheader("Portfolio Baseline")
try:
    portfolio_df = pipeline.portfolio_df
    total_val = portfolio_df["carrying_value_usd"].sum()
    st.sidebar.metric("Total Book Value", f"\${total_val:,.0f}")
    st.sidebar.metric("Active Positions", len(portfolio_df))
    st.sidebar.caption("Asset classes: Corporate Loans, Fixed-Rate Bonds, IR Swaps")
except Exception as e:
    st.sidebar.error(f"Failed to load baseline portfolio: {e}")

# Helper: Visual Display
def render_results(result: dict):
    signal = result["signal"]
    assessment = result["assessment"]
    stress = result["stress_result"]

    st.subheader("Event Summary")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Sentiment Score", f"{signal.sentiment_score:+.2f}")
    with c2:
        st.metric("Event Category", signal.event_category)
    with c3:
        st.metric("Severity (1-10)", f"{signal.severity_score}/10")
    with c4:
        tier = assessment.mapping_status
        badge_cls = {"DIRECT": "badge-direct", "SECTOR": "badge-sector", "MACRO": "badge-macro"}.get(tier, "badge-none")
        st.markdown(f"**Exposure Tier**<br><span class='status-badge {badge_cls}'>{tier}</span>", unsafe_allow_html=True)

    with st.expander("Analysis & Extracted Evidence", expanded=True):
        st.write(f"**Headline:** {signal.headline}")
        st.write(f"**Event Subtype:** `{signal.event_subtype}` | **Engine Mode:** `{signal.model_used}`")
        st.write(f"**Key Excerpt:** *\"{signal.evidence_quote}\"*")
        st.write(f"**Entity Detected:** {signal.extracted_entity or 'None'} | **Sector:** {signal.extracted_sector or 'None'}")
        st.write(f"**Mapping Note:** {assessment.mapping_rationale}")

    st.divider()

    st.subheader("Stress Test P&L Impact")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total P&L Shock", f"\${stress.total_loss_usd:,.0f}", delta=f"-{(stress.total_loss_usd/total_val)*100:.2f}%", delta_color="inverse")
    with m2:
        st.metric("Loan Credit Loss (ΔECL)", f"\${stress.incremental_ecl_usd:,.0f}")
    with m3:
        st.metric("Bond Value Change", f"\${stress.bond_loss_usd:,.0f}")
    with m4:
        st.metric("Swap Value Change", f"\${stress.swap_loss_usd:,.0f}")

    tab1, tab2, tab3 = st.tabs(["Position Level Impact", "Scenario Details", "Raw JSON Payload"])

    with tab1:
        pos_df = pd.DataFrame([p.model_dump() for p in stress.positions])
        if not pos_df.empty:
            affected = pos_df[pos_df["stress_loss_usd"] != 0]
            if not affected.empty:
                st.dataframe(
                    affected[["position_id", "asset_type", "counterparty_name", "sector", "carrying_value_usd", "stress_loss_usd", "loss_pct", "calculation_detail"]]
                    .style.format({"carrying_value_usd": "${:,.0f}", "stress_loss_usd": "${:,.0f}", "loss_pct": "{:.2f}%"}),
                    use_container_width=True,
                )
                fig = px.bar(
                    affected, x="counterparty_name", y="stress_loss_usd", color="asset_type",
                    title="Loss Attribution by Issuer / Asset Class",
                    labels={"stress_loss_usd": "P&L Impact (\$)", "counterparty_name": "Counterparty"},
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No direct or indirect exposures impacted by this event.")
        else:
            st.info("No positions available.")

    with tab2:
        s_info = stress.scenario_applied
        st.write(f"**Applied Scenario:** `{s_info.scenario_id}` ({s_info.name})")
        st.write(f"**Description:** {s_info.description}")
        st.json(s_info.model_dump()["shocks"])

    with tab3:
        st.json(result["export_payload"])

# Main Flow Router
if mode == "Interactive Analysis":
    st.subheader("Manual Headline Screening")
    sample_text = "Federal Reserve signals aggressive 50 bps interest rate hike to combat sticky services inflation."
    user_input = st.text_area("Input Headline or Financial Wire Snippet:", value=sample_text, height=100)

    if st.button("Run Evaluation", type="primary") and user_input.strip():
        with st.status("Executing Signal2Stress Pipeline...", expanded=True) as status:
            st.write("📡 Ingesting text and applying canonical URL/text normalization...")
            time.sleep(0.2)
            st.write("🔍 Computing SHA-256 deduplication hash...")
            time.sleep(0.2)
            st.write("📊 Evaluating FinBERT sentiment (S = P(pos) - P(neg))...")
            time.sleep(0.2)
            st.write("📑 Extracting event category, subtype rules, severity, and evidence...")
            out = pipeline.process_text(user_input.strip(), source="Manual Input")
            st.write("🛡️ Validating Pydantic schema contract...")
            time.sleep(0.2)
            st.write("📉 Applying balance sheet shock calculations...")
            status.update(label="Analysis Complete. Rendering Risk Output.", state="complete", expanded=False)

        render_results(out)

elif mode == "Preset Scenarios":
    st.subheader("Curated Validation Scenarios")
    demo_df = pipeline.get_demo_cases()
    selected_idx = st.selectbox(
        "Choose an event from the evaluation registry:",
        range(len(demo_df)),
        format_func=lambda i: f"{demo_df.iloc[i]['headline'][:80]}... [{demo_df.iloc[i]['expected_tier']}]",
    )
    case = demo_df.iloc[selected_idx]

    if st.button("Evaluate Selected Case", type="primary"):
        with st.status("Executing Scenario Validation...", expanded=True) as status:
            st.write("📡 Ingesting test payload...")
            time.sleep(0.2)
            st.write("📑 Running Stage 2 NLP extraction and contract validation...")
            out = pipeline.process_text(case["headline"], source="Validation Suite")
            st.write("📉 Generating balance sheet shock variables...")
            status.update(label="Validation Complete.", state="complete", expanded=False)

        render_results(out)

elif mode == "Live Feed Stream":
    st.subheader("Replay Feed Engine")
    feed_df = feed_processor.get_feed_items()
    st.dataframe(feed_df[["source", "headline"]].head(8), use_container_width=True)

    if st.button("Process Next Ingestion Batch", type="primary"):
        results = feed_processor.process_pending_feed()
        st.success(f"Processed {len(results)} items through the pipeline.")
        for res in results:
            with st.expander(f"{res['signal'].headline} ({res['assessment'].mapping_status})"):
                render_results(res)