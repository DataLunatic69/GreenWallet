import streamlit as st
import os
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from dotenv import load_dotenv
import sys
import json
import re

# Add the absolute path to the onchain_agent directory
onchain_agent_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "onchain_agent", "src")
sys.path.append(onchain_agent_path)

# Import after path is set
from onchain_agent.crew import OnchainAgentCrew

# Load environment variables
load_dotenv()

# Configure the page with custom theme
st.set_page_config(
    page_title="Onchain AI Agent",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    .carbon-alert {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .carbon-warning {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .carbon-danger {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "api_keys_set" not in st.session_state:
    st.session_state.api_keys_set = False
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
if "report_data" not in st.session_state:
    st.session_state.report_data = None

# Main header
st.markdown('<div class="main-header"><h1>🌍 Onchain AI Agent</h1><p>Blockchain Portfolio & Carbon Footprint Analysis</p></div>', unsafe_allow_html=True)

# Sidebar Configuration

def create_sample_carbon_data():
    """Create sample data for preview"""
    return [
        {'network': 'Ethereum', 'transactions': 50, 'co2_kg': 0.005},
        {'network': 'Polygon', 'transactions': 120, 'co2_kg': 0.0108},
        {'network': 'Base', 'transactions': 80, 'co2_kg': 0.004}
    ]

def create_network_pie_chart(network_data):
    """Create pie chart for network emissions"""
    if not network_data:
        return None
    
    networks = [item['network'].title() for item in network_data]
    emissions = [item['co2_kg'] for item in network_data]
    
    fig = go.Figure(data=[go.Pie(
        labels=networks,
        values=emissions,
        hole=0.4,
        marker=dict(colors=px.colors.qualitative.Set3)
    )])
    
    fig.update_layout(
        title="CO2 Emissions by Network",
        height=400,
        showlegend=True
    )
    
    return fig

def create_equivalents_chart(equivalents):
    """Create bar chart for environmental equivalents"""
    categories = []
    values = []
    
    if 'trees' in equivalents:
        categories.append('Trees (1 year)')
        values.append(equivalents['trees'])
    if 'km_driven' in equivalents:
        categories.append('Km Driven')
        values.append(equivalents['km_driven'])
    if 'smartphone_charges' in equivalents:
        categories.append('Phone Charges')
        values.append(equivalents['smartphone_charges'])
    if 'led_hours' in equivalents:
        categories.append('LED Hours')
        values.append(equivalents['led_hours'])
    
    fig = go.Figure(data=[go.Bar(
        x=categories,
        y=values,
        marker=dict(color=['#2ecc71', '#e74c3c', '#3498db', '#f39c12'])
    )])
    
    fig.update_layout(
        title="Environmental Equivalents",
        yaxis_title="Units",
        height=400,
        showlegend=False
    )
    
    return fig



def extract_insights(report_text):
    """Extract key insights from report"""
    insights = {
        'findings': [],
        'actions': [],
        'risks': {}
    }
    
    try:
        # Extract critical insights
        critical_section = re.search(r'Critical insights:(.*?)(?=\n##|\*)', report_text, re.DOTALL | re.IGNORECASE)
        if critical_section:
            findings = re.findall(r'\d+\.\s*\*\*(.+?)\*\*', critical_section.group(1))
            insights['findings'] = findings[:5]
        
        # Extract action items
        action_section = re.search(r'Immediate actions:(.*?)(?=\n##|\*)', report_text, re.DOTALL | re.IGNORECASE)
        if action_section:
            actions = re.findall(r'-\s*(.+?)(?=\n-|\n\n|\Z)', action_section.group(1))
            insights['actions'] = [a.strip() for a in actions[:5]]
        
        # Extract risk metrics
        hhi_match = re.search(r'HHI.*?([0-9]+)', report_text, re.IGNORECASE)
        if hhi_match:
            insights['risks']['concentration'] = min(int(hhi_match.group(1)) / 100, 100)
    
    except Exception as e:
        print(f"Error extracting insights: {e}")
    
    return insights

def extract_carbon_data(report_text):
    """Extract carbon footprint data from report"""
    carbon_data = {}
    
    try:
        # Extract total emissions
        co2_match = re.search(r'Total CO2 Emissions[:\s]+([0-9.]+)\s*kg', report_text, re.IGNORECASE)
        if co2_match:
            carbon_data['total_co2_kg'] = float(co2_match.group(1))
        
        # Extract energy
        energy_match = re.search(r'Total Energy Consumed[:\s]+([0-9.]+)\s*kWh', report_text, re.IGNORECASE)
        if energy_match:
            carbon_data['total_energy_kwh'] = float(energy_match.group(1))
        
        # Extract transactions
        tx_match = re.search(r'Total Transactions[:\s]+([0-9,]+)', report_text, re.IGNORECASE)
        if tx_match:
            carbon_data['total_transactions'] = int(tx_match.group(1).replace(',', ''))
        
        # Calculate average
        if carbon_data.get('total_co2_kg') and carbon_data.get('total_transactions'):
            carbon_data['avg_per_tx'] = carbon_data['total_co2_kg'] / carbon_data['total_transactions']
        
        # Extract network data
        network_section = re.search(r'Emissions by Network(.*?)(?=\n##|\Z)', report_text, re.DOTALL | re.IGNORECASE)
        if network_section:
            network_data = []
            network_lines = re.findall(r'-\s*(\w+):\s*([0-9,]+)\s*txs.*?([0-9.]+)\s*kg\s*CO2', network_section.group(1))
            for network, txs, co2 in network_lines:
                network_data.append({
                    'network': network,
                    'transactions': int(txs.replace(',', '')),
                    'co2_kg': float(co2)
                })
            carbon_data['network_data'] = network_data
        
        # Extract equivalents
        equivalents = {}
        trees_match = re.search(r'trees needed.*?([0-9.]+)', report_text, re.IGNORECASE)
        if trees_match:
            equivalents['trees'] = float(trees_match.group(1))
        
        km_match = re.search(r'km driven.*?([0-9.]+)', report_text, re.IGNORECASE)
        if km_match:
            equivalents['km_driven'] = float(km_match.group(1))
        
        phone_match = re.search(r'smartphone charges.*?([0-9.]+)', report_text, re.IGNORECASE)
        if phone_match:
            equivalents['smartphone_charges'] = float(phone_match.group(1))
        
        bulb_match = re.search(r'LED bulb.*?([0-9.]+)', report_text, re.IGNORECASE)
        if bulb_match:
            equivalents['led_hours'] = float(bulb_match.group(1))
        
        if equivalents:
            carbon_data['equivalents'] = equivalents
        
        # Extract strategies (simplified)
        strategies = []
        strategy_matches = re.finditer(r'\*\*(.+?)\*\*.*?Priority:\s*(\w+).*?-\s*(.+?)(?:-|$)', report_text, re.DOTALL)
        for match in strategy_matches:
            strategies.append({
                'name': match.group(1).strip(),
                'priority': match.group(2).strip().lower(),
                'description': match.group(3).strip()[:200]
            })
        
        if strategies:
            carbon_data['strategies'] = strategies[:5]  # Limit to top 5
    
    except Exception as e:
        print(f"Error extracting carbon data: {e}")
    
    return carbon_data if carbon_data else None


def create_risk_gauge(risks):
    """Create risk gauge visualization"""
    concentration_risk = risks.get('concentration', 50)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=concentration_risk,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Concentration Risk"},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 33], 'color': "lightgreen"},
                {'range': [33, 66], 'color': "yellow"},
                {'range': [66, 100], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


with st.sidebar:
    st.title("⚙️ Configuration")
    
    # API Keys Section
    with st.expander("🔑 API Keys", expanded=True):
        st.info("API keys are stored in session memory only")
        
        zapper_api_key = st.text_input(
            "Zapper API Key",
            type="password",
            help="Required for blockchain data access"
        )
        groq_api_key = st.text_input(
            "GROQ API Key",
            type="password",
            help="Required for LLM access"
        )

        if zapper_api_key and groq_api_key:
            os.environ["ZAPPER_API_KEY"] = zapper_api_key
            os.environ["GROQ_API_KEY"] = groq_api_key
            st.session_state.api_keys_set = True
            st.success("✅ API keys configured")
        else:
            st.session_state.api_keys_set = False
    
    # Analysis Options
    with st.expander("🎯 Analysis Options", expanded=True):
        include_carbon = st.checkbox("Include Carbon Footprint Analysis", value=True)
        detailed_charts = st.checkbox("Show Detailed Charts", value=True)
        export_format = st.selectbox("Report Format", ["Markdown", "PDF (Coming Soon)"])
    
    # About Section
    with st.expander("ℹ️ About"):
        st.markdown("""
        **Onchain AI Agent** provides comprehensive analysis:
        
        - 💼 Portfolio composition
        - 📊 Transaction patterns  
        - 🌍 Carbon footprint assessment
        - 💡 Optimization strategies
        
        **Developer:** Emmanuel Ezeokeke
        - [LinkedIn](https://www.linkedin.com/in/emma-ezeokeke/)
        - [X / Twitter](https://x.com/Emarh_AI)
        
        Powered by CrewAI & Zapper API
        """)

# Main Content Area
tab1, tab2, tab3 = st.tabs(["📊 Analysis", "🌍 Carbon Dashboard", "📈 Insights"])

with tab1:
    st.header("Wallet Analysis")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        wallet_address = st.text_input(
            "Wallet Address",
            value="",
            placeholder="0x...",
            help="Enter any EVM-compatible wallet address"
        )
    
    with col2:
        networks = st.multiselect(
            "Networks",
            options=["ethereum", "polygon", "optimism", "arbitrum", "base", "avalanche", "bsc"],
            default=["ethereum", "polygon", "base"],
            help="Select blockchain networks to analyze"
        )
    
    networks_str = ",".join(networks)
    
    # Analysis button
    run_button = st.button(
        "🚀 Run Analysis",
        type="primary",
        disabled=not st.session_state.api_keys_set,
        use_container_width=True
    )
    
    if run_button:
        if not st.session_state.api_keys_set:
            st.error("Please configure your API keys in the sidebar first.")
        elif not wallet_address:
            st.error("Please enter a wallet address.")
        else:
            inputs = {
                'wallet_address': wallet_address,
                'networks': networks_str
            }
            
            Path("outputs").mkdir(exist_ok=True, parents=True)
            Path("memory").mkdir(exist_ok=True, parents=True)
            
            with st.status("Running comprehensive blockchain analysis...", expanded=True) as status:
                try:
                    st.write(f"Analyzing wallet: {wallet_address}")
                    st.write(f"Networks: {networks_str}")
                    if include_carbon:
                        st.write("Including carbon footprint analysis...")
                    
                    crew = OnchainAgentCrew()
                    result = crew.crew().kickoff(inputs=inputs)
                    
                    status.update(label="Analysis complete!", state="complete", expanded=False)
                    st.session_state.analysis_complete = True
                    
                    # Parse and store report data
                    try:
                        with open("outputs/onchain_intelligence_report.md", "r") as f:
                            st.session_state.report_data = f.read()
                    except Exception as e:
                        st.error(f"Error loading report: {str(e)}")
                    
                except Exception as e:
                    status.update(label=f"Error: {str(e)}", state="error")
                    st.error(f"An error occurred: {str(e)}")
    
    # Display results if analysis is complete
    if st.session_state.analysis_complete and st.session_state.report_data:
        st.markdown("---")
        st.markdown(st.session_state.report_data)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label="📥 Download Report (MD)",
                data=st.session_state.report_data,
                file_name="onchain_intelligence_report.md",
                mime="text/markdown",
                use_container_width=True
            )
        with col2:
            st.download_button(
                label="📊 Export Data (JSON)",
                data=json.dumps({"wallet": wallet_address, "networks": networks}, indent=2),
                file_name="analysis_data.json",
                mime="application/json",
                use_container_width=True
            )

with tab2:
    st.header("Carbon Footprint Dashboard")
    
    if st.session_state.analysis_complete and st.session_state.report_data:
        # Extract carbon data from report
        carbon_section = extract_carbon_data(st.session_state.report_data)
        
        if carbon_section:
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Total CO2 Emissions",
                    value=f"{carbon_section.get('total_co2_kg', 0):.4f} kg",
                    delta=f"{carbon_section.get('vs_average', 'N/A')}",
                    delta_color="inverse"
                )
            
            with col2:
                st.metric(
                    label="Energy Consumed",
                    value=f"{carbon_section.get('total_energy_kwh', 0):.4f} kWh",
                    delta=None
                )
            
            with col3:
                st.metric(
                    label="Transactions",
                    value=f"{carbon_section.get('total_transactions', 0):,}",
                    delta=None
                )
            
            with col4:
                st.metric(
                    label="Avg per Transaction",
                    value=f"{carbon_section.get('avg_per_tx', 0):.6f} kg",
                    delta=None
                )
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Network emissions pie chart
                if carbon_section.get('network_data'):
                    fig_pie = create_network_pie_chart(carbon_section['network_data'])
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Environmental equivalents
                if carbon_section.get('equivalents'):
                    fig_equiv = create_equivalents_chart(carbon_section['equivalents'])
                    st.plotly_chart(fig_equiv, use_container_width=True)
            
            # Reduction strategies
            st.subheader("Carbon Reduction Strategies")
            
            if carbon_section.get('strategies'):
                for idx, strategy in enumerate(carbon_section['strategies'], 1):
                    with st.expander(f"{idx}. {strategy['name']} - {strategy.get('priority', 'medium').upper()} Priority"):
                        st.write(strategy.get('description', ''))
                        
                        cols = st.columns(3)
                        if 'potential_reduction_kg' in strategy:
                            cols[0].metric("Potential Reduction", f"{strategy['potential_reduction_kg']:.4f} kg")
                        if 'reduction_percent' in strategy:
                            cols[1].metric("Reduction %", f"{strategy['reduction_percent']}%")
                        if 'cost_usd' in strategy:
                            cols[2].metric("Estimated Cost", f"${strategy['cost_usd']:.2f}")
            
            # Impact assessment
            total_co2 = carbon_section.get('total_co2_kg', 0)
            if total_co2 < 0.1:
                alert_class = "carbon-alert"
                icon = "✅"
                message = "Your carbon footprint is very low! Great job maintaining minimal environmental impact."
            elif total_co2 < 1.0:
                alert_class = "carbon-warning"
                icon = "⚠️"
                message = "Your carbon footprint is moderate. Consider implementing some reduction strategies."
            else:
                alert_class = "carbon-danger"
                icon = "🚨"
                message = "Your carbon footprint is significant. We strongly recommend implementing reduction strategies."
            
            st.markdown(f'<div class="{alert_class}"><strong>{icon} Assessment:</strong> {message}</div>', unsafe_allow_html=True)
        
        else:
            st.info("No carbon footprint data available. Run an analysis with carbon footprint enabled.")
    else:
        st.info("Run an analysis to see carbon footprint dashboard")
        
        # Show sample visualization
        st.subheader("Sample Dashboard Preview")
        sample_data = create_sample_carbon_data()
        fig_sample = create_network_pie_chart(sample_data)
        st.plotly_chart(fig_sample, use_container_width=True)

with tab3:
    st.header("Portfolio Insights & Recommendations")
    
    if st.session_state.analysis_complete and st.session_state.report_data:
        # Extract key insights
        insights = extract_insights(st.session_state.report_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Key Findings")
            if insights.get('findings'):
                for finding in insights['findings']:
                    st.markdown(f"- {finding}")
        
        with col2:
            st.subheader("Action Items")
            if insights.get('actions'):
                for action in insights['actions']:
                    st.markdown(f"- {action}")
        
        # Risk assessment
        st.subheader("Risk Dashboard")
        if insights.get('risks'):
            create_risk_gauge(insights['risks'])
    else:
        st.info("Run an analysis to see portfolio insights")

# Helper functions

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("Made with ❤️ using CrewAI and Streamlit")
with col2:
    st.caption("Environmental data: Post-merge Ethereum metrics")
with col3:
    st.caption("Version 2.0 - Carbon Edition")