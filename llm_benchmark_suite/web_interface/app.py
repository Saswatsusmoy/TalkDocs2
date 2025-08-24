"""
Streamlit web interface for the LLM Benchmarking Suite.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import time

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from utils.evaluator import BenchmarkEvaluator
from config import config, ModelConfig, BenchmarkConfigClassInstance


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="LLM Benchmarking Suite",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .leaderboard-table {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🤖 LLM Benchmarking Suite</h1>', unsafe_allow_html=True)
    
    # Sidebar
    sidebar = st.sidebar
    
    # Navigation
    page = sidebar.selectbox(
        "Navigation",
        ["🏠 Dashboard", "📊 Leaderboard", "🔬 Run Benchmarks", "📈 Model Comparison", "⚙️ Settings"]
    )
    
    # Initialize evaluator
    if 'evaluator' not in st.session_state:
        st.session_state.evaluator = BenchmarkEvaluator()
    
    # Page routing
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "📊 Leaderboard":
        show_leaderboard()
    elif page == "🔬 Run Benchmarks":
        show_run_benchmarks()
    elif page == "📈 Model Comparison":
        show_model_comparison()
    elif page == "⚙️ Settings":
        show_settings()


def show_dashboard():
    """Show the main dashboard."""
    st.header("📊 Dashboard")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Available Models", len(ModelConfig.list_models()))
    
    with col2:
        st.metric("Available Benchmarks", len(BenchmarkConfigClassInstance.list_benchmarks()))
    
    with col3:
        # Get recent results count
        try:
            recent_results = st.session_state.evaluator.get_benchmark_history("text-generation", limit=100)
            st.metric("Recent Results", len(recent_results))
        except:
            st.metric("Recent Results", 0)
    
    with col4:
        st.metric("System Status", "🟢 Online")
    
    # Recent activity
    st.subheader("Recent Activity")
    
    try:
        # Get recent benchmark results
        recent_results = st.session_state.evaluator.get_benchmark_history("text-generation", limit=10)
        
        if recent_results:
            df = pd.DataFrame(recent_results)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp', ascending=False)
            
            # Display recent results
            for _, row in df.head(5).iterrows():
                with st.expander(f"{row['model_name']} - {row['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                    st.json(row['metrics'])
        else:
            st.info("No recent benchmark results found.")
    
    except Exception as e:
        st.error(f"Error loading recent activity: {e}")
    
    # Quick actions
    st.subheader("Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Run Quick Benchmark"):
            st.session_state.run_quick_benchmark = True
            st.rerun()
    
    with col2:
        if st.button("📊 View Leaderboard"):
            st.session_state.show_leaderboard = True
            st.rerun()


def show_leaderboard():
    """Show the leaderboard page."""
    st.header("📊 Leaderboard")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        benchmark_name = st.selectbox(
            "Benchmark",
            ["All"] + BenchmarkConfigClassInstance.list_benchmarks()
        )
    
    with col2:
        metric_name = st.selectbox(
            "Metric",
            ["All", "rouge1", "rouge2", "rougeL", "bleu", "accuracy", "f1", "exact_match"]
        )
    
    with col3:
        limit = st.slider("Top N", 5, 50, 10)
    
    # Get leaderboard data
    try:
        if benchmark_name == "All":
            # Show leaderboard for all benchmarks
            all_leaderboards = {}
            for bench in BenchmarkConfigClassInstance.list_benchmarks():
                leaderboard = st.session_state.evaluator.get_leaderboard(bench, None, limit)
                if leaderboard:
                    all_leaderboards[bench] = leaderboard
            
            # Display each benchmark's leaderboard
            for bench_name, leaderboard in all_leaderboards.items():
                st.subheader(f"🏆 {bench_name.replace('-', ' ').title()}")
                display_leaderboard_table(leaderboard)
        else:
            # Show leaderboard for specific benchmark
            leaderboard = st.session_state.evaluator.get_leaderboard(
                benchmark_name, 
                None if metric_name == "All" else metric_name, 
                limit
            )
            
            if leaderboard:
                st.subheader(f"🏆 {benchmark_name.replace('-', ' ').title()} Leaderboard")
                display_leaderboard_table(leaderboard)
                
                # Create visualization
                create_leaderboard_chart(leaderboard, benchmark_name)
            else:
                st.info(f"No results found for benchmark '{benchmark_name}'")
    
    except Exception as e:
        st.error(f"Error loading leaderboard: {e}")


def display_leaderboard_table(leaderboard: List[Dict[str, Any]]):
    """Display leaderboard as a table."""
    if not leaderboard:
        st.info("No leaderboard data available.")
        return
    
    # Create DataFrame
    df = pd.DataFrame(leaderboard)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Format the table
    st.dataframe(
        df[['rank', 'model_name', 'metric_name', 'metric_value', 'timestamp']].rename(
            columns={
                'rank': 'Rank',
                'model_name': 'Model',
                'metric_name': 'Metric',
                'metric_value': 'Score',
                'timestamp': 'Date'
            }
        ),
        use_container_width=True,
        hide_index=True
    )


def create_leaderboard_chart(leaderboard: List[Dict[str, Any]], benchmark_name: str):
    """Create a chart visualization of the leaderboard."""
    if not leaderboard:
        return
    
    df = pd.DataFrame(leaderboard)
    
    # Create bar chart
    fig = px.bar(
        df,
        x='model_name',
        y='metric_value',
        color='metric_name',
        title=f"{benchmark_name.replace('-', ' ').title()} Leaderboard",
        labels={'model_name': 'Model', 'metric_value': 'Score', 'metric_name': 'Metric'},
        barmode='group'
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_run_benchmarks():
    """Show the run benchmarks page."""
    st.header("🔬 Run Benchmarks")
    
    # Model selection
    st.subheader("Model Selection")
    model_name = st.selectbox("Select Model", ModelConfig.list_models())
    
    # Benchmark selection
    st.subheader("Benchmark Selection")
    benchmark_name = st.selectbox("Select Benchmark", BenchmarkConfigClassInstance.list_benchmarks())
    
    # Get benchmark info
    benchmark_info = BenchmarkConfigClassInstance.get_benchmark_info(benchmark_name)
    if benchmark_info:
        st.info(f"**{benchmark_info['name']}**: {benchmark_info['description']}")
    
    # Configuration
    st.subheader("Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_samples = st.slider("Number of Samples", 1, 1000, config.num_samples)
        dataset_name = st.text_input("Dataset Name (optional)", value="")
    
    with col2:
        save_results = st.checkbox("Save Results", value=True)
        verbose_output = st.checkbox("Verbose Output", value=False)
    
    # Run button
    if st.button("🚀 Run Benchmark", type="primary"):
        if st.button:
            run_benchmark(model_name, benchmark_name, dataset_name, num_samples, save_results, verbose_output)


def run_benchmark(model_name: str, benchmark_name: str, dataset_name: str, 
                 num_samples: int, save_results: bool, verbose_output: bool):
    """Run a benchmark and display results."""
    st.subheader("Running Benchmark...")
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Update status
        status_text.text("Loading model...")
        progress_bar.progress(25)
        
        # Run benchmark
        status_text.text("Running inference...")
        progress_bar.progress(50)
        
        result = st.session_state.evaluator.run_benchmark(
            model_name=model_name,
            benchmark_name=benchmark_name,
            dataset_name=dataset_name if dataset_name else None,
            num_samples=num_samples,
            save_results=save_results
        )
        
        progress_bar.progress(100)
        status_text.text("Complete!")
        
        # Display results
        st.subheader("📊 Results")
        
        # Metrics
        metrics = result.get('metrics', {})
        if metrics:
            st.subheader("Metrics")
            
            # Create metric cards
            cols = st.columns(len(metrics))
            for i, (metric_name, metric_value) in enumerate(metrics.items()):
                with cols[i]:
                    st.metric(metric_name.replace('_', ' ').title(), f"{metric_value:.4f}")
        
        # Detailed results
        if verbose_output:
            st.subheader("Detailed Results")
            st.json(result)
        
        # Success message
        st.success(f"✅ Benchmark completed successfully!")
        
        # Show leaderboard update
        st.subheader("🏆 Updated Leaderboard")
        leaderboard = st.session_state.evaluator.get_leaderboard(benchmark_name, limit=5)
        if leaderboard:
            display_leaderboard_table(leaderboard)
    
    except Exception as e:
        st.error(f"❌ Error running benchmark: {e}")
        if verbose_output:
            st.exception(e)


def show_model_comparison():
    """Show the model comparison page."""
    st.header("📈 Model Comparison")
    
    # Model selection
    st.subheader("Model Selection")
    selected_models = st.multiselect(
        "Select Models to Compare",
        ModelConfig.list_models(),
        default=ModelConfig.list_models()[:3]
    )
    
    # Benchmark selection
    benchmark_name = st.selectbox("Select Benchmark", BenchmarkConfigClassInstance.list_benchmarks())
    
    # Configuration
    num_samples = st.slider("Number of Samples", 1, 500, 50)
    
    # Run comparison
    if st.button("🔬 Compare Models", type="primary"):
        if len(selected_models) < 2:
            st.warning("Please select at least 2 models to compare.")
        else:
            compare_models(selected_models, benchmark_name, num_samples)


def compare_models(model_names: List[str], benchmark_name: str, num_samples: int):
    """Compare multiple models and display results."""
    st.subheader("Running Model Comparison...")
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Run comparison
        status_text.text("Running benchmarks...")
        results = st.session_state.evaluator.compare_models(model_names, benchmark_name, num_samples)
        
        progress_bar.progress(100)
        status_text.text("Complete!")
        
        # Display comparison results
        st.subheader("📊 Comparison Results")
        
        # Create comparison table
        comparison_data = []
        for model_name, result in results.items():
            if "error" in result:
                comparison_data.append({
                    "Model": model_name,
                    "Status": "❌ Error",
                    "Error": result["error"]
                })
            else:
                metrics = result.get("metrics", {})
                for metric_name, metric_value in metrics.items():
                    comparison_data.append({
                        "Model": model_name,
                        "Metric": metric_name.replace("_", " ").title(),
                        "Value": f"{metric_value:.4f}",
                        "Status": "✅ Success"
                    })
        
        if comparison_data:
            df = pd.DataFrame(comparison_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Create comparison chart
            create_comparison_chart(results, benchmark_name)
        else:
            st.info("No comparison data available.")
    
    except Exception as e:
        st.error(f"❌ Error comparing models: {e}")


def create_comparison_chart(results: Dict[str, Any], benchmark_name: str):
    """Create a comparison chart."""
    # Prepare data for charting
    chart_data = []
    
    for model_name, result in results.items():
        if "error" not in result:
            metrics = result.get("metrics", {})
            for metric_name, metric_value in metrics.items():
                chart_data.append({
                    "Model": model_name,
                    "Metric": metric_name.replace("_", " ").title(),
                    "Value": metric_value
                })
    
    if not chart_data:
        return
    
    df = pd.DataFrame(chart_data)
    
    # Create bar chart
    fig = px.bar(
        df,
        x="Model",
        y="Value",
        color="Metric",
        title=f"Model Comparison - {benchmark_name.replace('-', ' ').title()}",
        barmode="group"
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_settings():
    """Show the settings page."""
    st.header("⚙️ Settings")
    
    st.subheader("Configuration")
    
    # Display current configuration
    st.json({
        "Database URL": config.database_url,
        "Device": config.default_device,
        "Max Length": config.max_length,
        "Batch Size": config.batch_size,
        "Num Samples": config.num_samples,
        "Timeout Seconds": config.timeout_seconds,
        "Results Directory": config.results_dir
    })
    
    st.subheader("System Information")
    
    # Memory usage
    try:
        memory_info = st.session_state.evaluator.model_loader.get_memory_usage()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("System Memory Used", f"{memory_info.get('system_used_gb', 0):.1f} GB")
            st.metric("System Memory Available", f"{memory_info.get('system_available_gb', 0):.1f} GB")
        
        with col2:
            if 'gpu_total_gb' in memory_info:
                st.metric("GPU Memory Used", f"{memory_info.get('gpu_allocated_gb', 0):.1f} GB")
                st.metric("GPU Memory Total", f"{memory_info.get('gpu_total_gb', 0):.1f} GB")
            else:
                st.info("GPU not available")
    
    except Exception as e:
        st.error(f"Error getting system information: {e}")
    
    # Loaded models
    st.subheader("Loaded Models")
    loaded_models = st.session_state.evaluator.model_loader.list_loaded_models()
    
    if loaded_models:
        for model in loaded_models:
            metadata = st.session_state.evaluator.model_loader.get_model_metadata(model)
            with st.expander(f"📦 {model}"):
                st.json(metadata)
    else:
        st.info("No models currently loaded.")


if __name__ == "__main__":
    main()
