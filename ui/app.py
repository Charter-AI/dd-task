"""Streamlit UI for DD Analytics Agent."""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import json
from datetime import datetime

from dd_agent.orchestrator.pipeline import Pipeline
from dd_agent.orchestrator.agent import Agent
from dd_agent.contracts.questions import Question
import pandas as pd
import json

# Page configuration
st.set_page_config(
    page_title="DD Analytics Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #D1FAE5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10B981;
    }
    .error-box {
        background-color: #FEE2E2;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #EF4444;
    }
    .metric-card {
        background-color: #F8FAFC;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

def load_data():
    """Load demo data."""
    data_dir = Path('data/demo')
    
    # Load questions
    with open(data_dir / 'questions.json') as f:
        questions_data = json.load(f)
        questions = [Question.model_validate(q) for q in questions_data]
    
    # Load responses
    responses_df = pd.read_csv(data_dir / 'responses.csv')
    
    return questions, responses_df, data_dir

def main():
    """Main application."""
    st.markdown('<h1 class="main-header">📊 DD Analytics Agent</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'agent' not in st.session_state:
        st.session_state.questions, st.session_state.responses_df, st.session_state.data_dir = load_data()
        st.session_state.agent = Agent(
            questions=st.session_state.questions,
            responses_df=st.session_state.responses_df,
            data_dir=st.session_state.data_dir
        )
        st.session_state.segments = []
        st.session_state.runs = []
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Go to",
            ["📈 Quick Analysis", "🔍 Segment Builder", "📋 Run History", "ℹ️ About"]
        )
        
        st.divider()
        
        st.header("Dataset Info")
        st.write(f"**Questions**: {len(st.session_state.questions)}")
        st.write(f"**Responses**: {len(st.session_state.responses_df)}")
        
        if st.session_state.segments:
            st.divider()
            st.header("Active Segments")
            for segment in st.session_state.segments[-5:]:  # Show last 5
                st.caption(f"📍 {segment.name}")
    
    # Page routing
    if page == "📈 Quick Analysis":
        show_quick_analysis()
    elif page == "🔍 Segment Builder":
        show_segment_builder()
    elif page == "📋 Run History":
        show_run_history()
    elif page == "ℹ️ About":
        show_about()

def show_quick_analysis():
    """Quick analysis page."""
    st.header("Quick Analysis")
    
    # Example queries
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Show NPS by region", use_container_width=True):
            st.session_state.query = "Show NPS by region"
    with col2:
        if st.button("Compare satisfaction by plan", use_container_width=True):
            st.session_state.query = "Compare overall satisfaction by subscription plan"
    with col3:
        if st.button("Analyze feature usage", use_container_width=True):
            st.session_state.query = "Show feature usage frequency"
    
    # Query input
    query = st.text_area(
        "Enter your analysis request:",
        value=getattr(st.session_state, 'query', 'Show NPS by region'),
        height=100,
        placeholder="E.g., 'Show NPS by region' or 'Compare satisfaction by income level'"
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        run_analysis = st.button("🚀 Run Analysis", type="primary", use_container_width=True)
    with col2:
        run_autoplan = st.button("🤖 Auto-Plan", use_container_width=True)
    
    if run_analysis:
        with st.spinner("Analyzing..."):
            try:
                pipeline = Pipeline(st.session_state.data_dir)
                result = pipeline.run_single(query, save_run=True)
                
                if result.success:
                    st.markdown('<div class="success-box">✅ Analysis completed successfully!</div>', unsafe_allow_html=True)
                    
                    # Display results
                    if result.execution_result and result.execution_result.tables:
                        table = result.execution_result.tables[0]
                        
                        # Metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Metric", table.metric_type)
                        with col2:
                            st.metric("Question", table.question_id)
                        with col3:
                            st.metric("Base Size", table.base_n)
                        
                        # Display data
                        if hasattr(table, 'df') and table.df is not None:
                            st.subheader("Results")
                            
                            # Table view
                            st.dataframe(table.df, use_container_width=True)
                            
                            # Chart view
                            if 'dimension' in table.df.columns and 'metric' in table.df.columns:
                                fig = px.bar(
                                    table.df,
                                    x='dimension',
                                    y='metric',
                                    title=f"{table.metric_type} by {table.df['dimension'].iloc[0] if not table.df.empty else 'Dimension'}",
                                    labels={'metric': table.metric_type, 'dimension': 'Dimension'}
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        
                        # Save to session history
                        st.session_state.runs.append({
                            'timestamp': datetime.now().isoformat(),
                            'query': query,
                            'run_id': result.run_id,
                            'success': True
                        })
                        
                else:
                    st.markdown('<div class="error-box">❌ Analysis failed</div>', unsafe_allow_html=True)
                    for error in result.errors:
                        st.error(error)
                        
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    elif run_autoplan:
        with st.spinner("Generating comprehensive analysis plan..."):
            try:
                pipeline = Pipeline(st.session_state.data_dir)
                result = pipeline.run_autoplan(save_run=True, max_cuts=5)
                
                if result.success:
                    st.markdown('<div class="success-box">🤖 Auto-plan completed!</div>', unsafe_allow_html=True)
                    
                    st.subheader("Analysis Plan")
                    if result.plan:
                        st.write(f"**Rationale**: {result.plan.rationale}")
                        
                        for i, intent in enumerate(result.plan.intents):
                            with st.expander(f"Intent {i+1}: {intent.description}"):
                                st.write(f"**Priority**: {'🔴 High' if intent.priority == 1 else '🟡 Medium' if intent.priority == 2 else '🟢 Low'}")
                                if intent.segments_needed:
                                    st.write(f"**Segments needed**: {', '.join(intent.segments_needed)}")
                    
                    st.subheader("Execution Summary")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Cuts Executed", len(result.cuts_planned))
                    with col2:
                        st.metric("Cuts Failed", len(result.cuts_failed))
                    with col3:
                        st.metric("Tables Generated", len(result.execution_result.tables) if result.execution_result else 0)
                        
                    # Save to session history
                    st.session_state.runs.append({
                        'timestamp': datetime.now().isoformat(),
                        'query': 'Auto-plan',
                        'run_id': result.run_id,
                        'success': True
                    })
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")

def show_segment_builder():
    """Segment builder page."""
    st.header("Segment Builder")
    
    st.write("Create custom segments for advanced analysis")
    
    # Example segment definitions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏢 Enterprise customers", use_container_width=True):
            st.session_state.segment_def = "Enterprise customers on ENT plan"
    with col2:
        if st.button("⭐ Promoters (NPS 9-10)", use_container_width=True):
            st.session_state.segment_def = "Promoters with NPS 9-10"
    
    # Segment definition input
    segment_def = st.text_area(
        "Define your segment:",
        value=getattr(st.session_state, 'segment_def', 'Enterprise customers on ENT plan'),
        height=100,
        placeholder="E.g., 'Users aged 25-34 with high income' or 'Customers using Dashboard and Reporting features'"
    )
    
    if st.button("Build Segment", type="primary"):
        with st.spinner("Building segment..."):
            try:
                result = st.session_state.agent.build_segment(segment_def)
                
                if result.ok and result.data:
                    segment = result.data
                    st.markdown('<div class="success-box">✅ Segment created successfully!</div>', unsafe_allow_html=True)
                    
                    # Display segment info
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Segment ID", segment.segment_id)
                    with col2:
                        st.metric("Name", segment.name)
                    
                    st.write("**Definition**:")
                    st.code(json.dumps(segment.definition.model_dump(), indent=2), language='json')
                    
                    if segment.notes:
                        st.write(f"**Notes**: {segment.notes}")
                    
                    # Add to session segments
                    st.session_state.segments.append(segment)
                    st.session_state.agent.add_segment(segment)
                    
                    # Show segment size
                    mask = st.session_state.agent.execute_cuts([])  # Just to get executor
                    # This would need actual computation
                    
                else:
                    st.markdown('<div class="error-box">❌ Failed to create segment</div>', unsafe_allow_html=True)
                    for error in result.errors:
                        st.error(str(error))
                        
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # List existing segments
    if st.session_state.segments:
        st.divider()
        st.subheader("Existing Segments")
        
        for segment in st.session_state.segments:
            with st.expander(f"📍 {segment.name}"):
                st.write(f"**ID**: {segment.segment_id}")
                st.write(f"**Definition**: `{segment.definition.__class__.__name__}`")
                if segment.notes:
                    st.write(f"**Notes**: {segment.notes}")

def show_run_history():
    """Run history page."""
    st.header("Run History")
    
    if not st.session_state.runs:
        st.info("No runs yet. Run an analysis to see history here.")
        return
    
    # Display runs in reverse chronological order
    for run in reversed(st.session_state.runs):
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**Query**: {run['query'][:100]}{'...' if len(run['query']) > 100 else ''}")
                st.caption(f"Run ID: {run['run_id']} • {run['timestamp'][:19]}")
            with col2:
                st.write("✅ Success" if run['success'] else "❌ Failed")
            with col3:
                if st.button("View", key=run['run_id']):
                    st.info("View functionality would show detailed results here")

def show_about():
    """About page."""
    st.header("About DD Analytics Agent")
    
    st.write("""
    This is a production-grade analytics agent for survey data analysis.
    
    ## Features
    
    ### 🤖 Intelligent Analysis
    - Natural language to structured analysis specifications
    - Automatic metric inference (NPS, top2box, mean, etc.)
    - Comprehensive auto-planning
    
    ### 🔍 Advanced Segmentation
    - Create custom segments from natural language
    - Use segments as dimensions or filters
    - Combine multiple criteria with logical operators
    
    ### 📊 Deterministic Execution
    - LLM plans, Python (Pandas) computes
    - Reproducible results
    - Validated outputs
    
    ### 📁 Complete Traceability
    - Full audit trail of every analysis
    - Structured artifacts (JSON, CSV)
    - Human-readable reports
    
    ## Architecture
    
    The system follows a **tool-based architecture**:
    
    1. **High-Level Planner** - Creates comprehensive analysis plans
    2. **Cut Planner** - Converts NL requests to CutSpecs
    3. **Segment Builder** - Creates segments from NL definitions
    4. **Executor** - Deterministic Pandas execution engine
    5. **Agent** - Orchestrates tools and execution
    6. **Pipeline** - End-to-end workflow management
    
    ## Example Use Cases
    
    - "Show NPS by region"
    - "Create enterprise segment and compare satisfaction"
    - "Analyze feature usage patterns"
    - "Identify at-risk customers"
    """)
    
    st.divider()
    
    st.subheader("Technical Details")
    st.write("""
    - **Backend**: Python 3.11+, Pydantic, Pandas
    - **LLM**: Azure OpenAI with structured outputs
    - **Storage**: JSON artifacts, CSV results
    - **Validation**: Strict schema validation
    """)

if __name__ == "__main__":
    main()