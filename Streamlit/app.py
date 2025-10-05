import streamlit as st
import os
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from dotenv import load_dotenv
import sys
import json
import re

# Note: Encoding issues should be handled at the system level

# Add the absolute path to the onchain_agent directory
onchain_agent_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "onchain_agent", "src")
sys.path.append(onchain_agent_path)

from onchain_agent.crew import OnchainAgentCrew

load_dotenv()

# Configure the page
st.set_page_config(
    page_title="Green Wallet - Carbon Analytics",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS (same as before)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1419 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Global text contrast fixes */
    * {
        color: #ffffff !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #28a745 !important;
    }
    
    .stMarkdown, .stMarkdown * {
        color: #ffffff !important;
    }
    
    p, div, span, li, ul, ol {
        color: #ffffff !important;
    }
    
    /* Ensure all text outside bubbles is white */
    .main .block-container {
        color: #ffffff !important;
    }
    
    .main .block-container * {
        color: #ffffff !important;
    }
    
    .hero-header {
        position: relative;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%),
                    url('https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&h=400&fit=crop') center/cover;
        border-radius: 20px;
        margin-bottom: 2rem;
        overflow: hidden;
        box-shadow: 0 20px 60px rgba(34, 197, 94, 0.3);
    }
    
    .hero-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(6, 78, 59, 0.95) 0%, rgba(16, 185, 129, 0.95) 100%);
        z-index: 1;
    }
    
    .hero-content {
        position: relative;
        z-index: 2;
        text-align: center;
        color: white;
    }
    
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #22c55e 0%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { filter: drop-shadow(0 0 5px rgba(34, 197, 94, 0.5)); }
        to { filter: drop-shadow(0 0 20px rgba(34, 197, 94, 0.8)); }
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        color: #d1d5db;
        font-weight: 300;
        letter-spacing: 1px;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(16, 185, 129, 0.3);
        border-color: rgba(16, 185, 129, 0.5);
    }
    
    .status-alert {
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        border-left: 4px solid;
        backdrop-filter: blur(10px);
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .carbon-low {
        background: rgba(16, 185, 129, 0.1);
        border-left-color: #10b981;
        color: #d1fae5;
    }
    
    .carbon-medium {
        background: rgba(251, 191, 36, 0.1);
        border-left-color: #fbbf24;
        color: #fef3c7;
    }
    
    .carbon-high {
        background: rgba(239, 68, 68, 0.1);
        border-left-color: #ef4444;
        color: #fee2e2;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.05);
        padding: 0.5rem;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #9ca3af;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(16, 185, 129, 0.1);
        color: #10b981;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #10b981 0%, #6366f1 100%);
        color: white !important;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6);
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #10b981 0%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .network-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid #10b981;
        border-radius: 20px;
        color: #10b981;
        font-size: 0.875rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .footer {
        margin-top: 3rem;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.02);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        text-align: center;
        color: #9ca3af;
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

# Hero Header
st.markdown("""
<div class="hero-header">
    <div class="hero-content">
        <h1 class="hero-title">🌱 Green Wallet</h1>
        <p class="hero-subtitle">Sustainable Blockchain Portfolio Intelligence & Carbon Footprint Analytics</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Helper Functions
def create_animated_network_chart(network_data):
    """Create animated donut chart for network emissions"""
    if not network_data:
        return None
    
    networks = [item['network'].title() for item in network_data]
    emissions = [item['co2_kg'] for item in network_data]
    
    colors = ['#10b981', '#6366f1', '#8b5cf6', '#ec4899', '#f59e0b']
    
    fig = go.Figure(data=[go.Pie(
        labels=networks,
        values=emissions,
        hole=0.6,
        marker=dict(colors=colors[:len(networks)], line=dict(color='#0a0e27', width=2)),
        textinfo='label+percent',
        textfont=dict(size=14, color='white'),
        hovertemplate='<b>%{label}</b><br>Emissions: %{value:.4f} kg CO2<extra></extra>'
    )])
    
    fig.update_layout(
        title={'text': 'CO2 Emissions by Network', 'font': {'size': 20, 'color': '#e2e8f0'}},
        height=450,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(font=dict(color='#e2e8f0'), bgcolor='rgba(255,255,255,0.05)'),
        annotations=[dict(
            text=f'{sum(emissions):.4f}<br>kg CO2',
            x=0.5, y=0.5,
            font=dict(size=20, color='#10b981'),
            showarrow=False
        )]
    )
    
    return fig

def create_equivalents_chart(equivalents):
    """Create modern bar chart for environmental equivalents"""
    data = []
    if 'trees' in equivalents:
        data.append({'category': '🌳 Trees (1 year)', 'value': equivalents['trees'], 'color': '#10b981'})
    if 'km_driven' in equivalents:
        data.append({'category': '🚗 Km Driven', 'value': equivalents['km_driven'], 'color': '#ef4444'})
    if 'smartphone_charges' in equivalents:
        data.append({'category': '📱 Phone Charges', 'value': equivalents['smartphone_charges'], 'color': '#3b82f6'})
    if 'led_hours' in equivalents:
        data.append({'category': '💡 LED Hours', 'value': equivalents['led_hours'], 'color': '#f59e0b'})
    
    categories = [d['category'] for d in data]
    values = [d['value'] for d in data]
    colors = [d['color'] for d in data]
    
    fig = go.Figure(data=[go.Bar(
        y=categories,
        x=values,
        orientation='h',
        marker=dict(color=colors),
        text=[f'{v:.1f}' for v in values],
        textposition='outside',
        textfont=dict(color='white', size=14)
    )])
    
    fig.update_layout(
        title={'text': '🌱 Green Impact Equivalents', 'font': {'size': 20, 'color': '#e2e8f0'}},
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='#9ca3af'),
        yaxis=dict(showgrid=False, color='#e2e8f0')
    )
    
    return fig

def extract_carbon_data(report_text):
    """Extract carbon footprint data from report"""
    carbon_data = {}
    
    try:
        co2_match = re.search(r'Total CO2 Emissions[:\s]+([0-9.]+)\s*kg', report_text, re.IGNORECASE)
        if co2_match:
            carbon_data['total_co2_kg'] = float(co2_match.group(1))
        
        energy_match = re.search(r'Total Energy Consumed[:\s]+([0-9.]+)\s*kWh', report_text, re.IGNORECASE)
        if energy_match:
            carbon_data['total_energy_kwh'] = float(energy_match.group(1))
        
        tx_match = re.search(r'Total [Tt]ransactions[:\s]+([0-9,]+)', report_text, re.IGNORECASE)
        if tx_match:
            carbon_data['total_transactions'] = int(tx_match.group(1).replace(',', ''))
        
        if carbon_data.get('total_co2_kg') and carbon_data.get('total_transactions'):
            carbon_data['avg_per_tx'] = carbon_data['total_co2_kg'] / carbon_data['total_transactions']
        
        network_section = re.search(r'Emissions by [Nn]etwork(.*?)(?=\n##|\Z)', report_text, re.DOTALL)
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
        
        equivalents = {}
        trees_match = re.search(r'trees.*?([0-9.]+)', report_text, re.IGNORECASE)
        if trees_match:
            equivalents['trees'] = float(trees_match.group(1))
        
        km_match = re.search(r'km driven.*?([0-9.]+)', report_text, re.IGNORECASE)
        if km_match:
            equivalents['km_driven'] = float(km_match.group(1))
        
        phone_match = re.search(r'smartphone.*?([0-9.]+)', report_text, re.IGNORECASE)
        if phone_match:
            equivalents['smartphone_charges'] = float(phone_match.group(1))
        
        bulb_match = re.search(r'LED.*?([0-9.]+)', report_text, re.IGNORECASE)
        if bulb_match:
            equivalents['led_hours'] = float(bulb_match.group(1))
        
        if equivalents:
            carbon_data['equivalents'] = equivalents
    
    except Exception as e:
        print(f"Error extracting carbon data: {e}")
    
    return carbon_data if carbon_data else None

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    with st.expander("🔑 API Keys", expanded=True):
        st.info("🔒 Keys stored in session only")
        
        zapper_api_key = st.text_input("Zapper API Key", type="password")
        openai_api_key = st.text_input("OpenAI API Key", type="password", help="Using GPT-3.5-turbo for cost-effective analysis")
        moralis_api_key = st.text_input("Moralis API Key", type="password")
        
        if openai_api_key:
            st.info("💰 Estimated cost per analysis: ~$0.02-0.05 (GPT-3.5-turbo)")

        if zapper_api_key and openai_api_key and moralis_api_key:
            os.environ["ZAPPER_API_KEY"] = zapper_api_key
            os.environ["OPENAI_API_KEY"] = openai_api_key
            os.environ["MORALIS_API_KEY"] = moralis_api_key
            st.session_state.api_keys_set = True
            st.success("✅ All keys configured")
        else:
            st.session_state.api_keys_set = False
            if not moralis_api_key:
                st.warning("⚠️ Moralis API key required for transaction history")
            if not openai_api_key:
                st.warning("⚠️ OpenAI API key required for AI analysis")
    
    with st.expander("🎯 Analysis Options", expanded=False):
        networks_to_analyze = st.multiselect(
            "Additional Networks",
            ["polygon", "bsc", "arbitrum", "optimism", "base", "avalanche"],
            default=[],
            help="Ethereum is always analyzed"
        )
    


# Main Tabs
tab1, tab2 = st.tabs(["📊 Analysis & Report", "🌍 Carbon Dashboard"])

with tab1:
    st.markdown("### Wallet Analysis")
    
    wallet_address = st.text_input(
        "Wallet Address",
        placeholder="0x...",
        help="Enter EVM-compatible address (Ethereum, Polygon, BSC, etc.)"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    run_button = st.button(
        "🚀 Run Carbon Analysis",
        type="primary",
        disabled=not st.session_state.api_keys_set,
        use_container_width=True
    )
    
    if run_button:
        if not wallet_address:
            st.error("Please enter a wallet address")
        elif not wallet_address.startswith("0x"):
            st.error("Please enter a valid EVM address (must start with 0x)")
        else:
            # Build networks string
            base_networks = ["ethereum"]
            all_networks = base_networks + networks_to_analyze
            networks_str = ",".join(all_networks)
            
            st.markdown(' '.join([f'<span class="network-badge">{net.upper()}</span>' for net in all_networks]), unsafe_allow_html=True)
            
            inputs = {'wallet_address': wallet_address, 'networks': networks_str}
            
            Path("outputs").mkdir(exist_ok=True, parents=True)
            Path("memory").mkdir(exist_ok=True, parents=True)
            
            with st.status("🔄 Running comprehensive analysis...", expanded=True) as status:
                try:
                    st.write(f"**Wallet:** {wallet_address}")
                    st.write(f"**Networks:** {networks_str}")
                    st.write("🌍 Calculating carbon footprint from transaction gas usage...")
                    
                    crew = OnchainAgentCrew()
                    result = crew.crew().kickoff(inputs=inputs)
                    
                    status.update(label="✅ Analysis complete!", state="complete", expanded=False)
                    st.session_state.analysis_complete = True
                    
                    with open("outputs/onchain_intelligence_report.md", "r") as f:
                        st.session_state.report_data = f.read()
                    
                    st.balloons()
                    
                except Exception as e:
                    status.update(label=f"❌ Error: {str(e)}", state="error")
                    st.error(f"An error occurred: {str(e)}")
    
    if st.session_state.analysis_complete and st.session_state.report_data:
        st.markdown("---")
        
        # Enhanced Report Display with Animations
        st.markdown("""
        <style>
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-50px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .report-container {
            animation: fadeInUp 0.8s ease-out;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .report-container:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.15);
        }
        
        .report-header {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            animation: slideInLeft 0.6s ease-out;
        }
        
        .report-header h2 {
            margin: 0;
            font-size: 1.8em;
            font-weight: 600;
        }
        
        .metric-card {
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 4px solid #28a745;
            animation: fadeInUp 0.8s ease-out;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            color: #333333 !important;
        }
        
        .metric-card:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 8px 25px rgba(40, 167, 69, 0.3);
        }
        
        .metric-card * {
            color: #333333 !important;
        }
        
        .metric-card h1, .metric-card h2, .metric-card h3, .metric-card h4, .metric-card h5, .metric-card h6 {
            color: #28a745 !important;
        }
        
        .highlight-box {
            background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%);
            border: 2px solid #28a745;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            animation: fadeInUp 0.8s ease-out;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            color: #155724 !important;
        }
        
        .highlight-box:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 8px 25px rgba(40, 167, 69, 0.3);
        }
        
        .highlight-box * {
            color: #155724 !important;
        }
        
        .highlight-box h1, .highlight-box h2, .highlight-box h3, .highlight-box h4, .highlight-box h5, .highlight-box h6 {
            color: #28a745 !important;
        }
        
        .section-header {
            color: #28a745;
            font-weight: 600;
            font-size: 1.3em;
            margin: 20px 0 10px 0;
            padding-bottom: 5px;
            border-bottom: 2px solid #28a745;
            animation: slideInLeft 0.6s ease-out;
            transition: transform 0.3s ease;
        }
        
        .section-header:hover {
            transform: translateX(5px);
        }
        
        .download-section {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
            color: #333333 !important;
            animation: fadeInUp 0.8s ease-out;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .download-section:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .download-section * {
            color: #333333 !important;
        }
        
        /* Ensure all text in report containers has proper contrast */
        .report-container {
            color: #333333 !important;
        }
        
        .report-container * {
            color: #333333 !important;
        }
        
        .report-container h1, .report-container h2, .report-container h3, 
        .report-container h4, .report-container h5, .report-container h6 {
            color: #28a745 !important;
        }
        
        /* Override Streamlit's default text colors */
        .stMarkdown {
            color: #333333 !important;
        }
        
        .stMarkdown * {
            color: #333333 !important;
        }
        
        /* Ensure proper contrast for all text elements */
        p, div, span, li, ul, ol {
            color: #333333 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Report Header with Animation
        st.markdown("""
        <div class="report-header">
            <h2>🌱 Green Wallet Analysis Report</h2>
            <p>Comprehensive blockchain portfolio intelligence & carbon footprint analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced Report Content
        st.markdown('<div class="report-container">', unsafe_allow_html=True)
        
        # Parse and display report with enhanced formatting
        report_sections = st.session_state.report_data.split('## ')
        for i, section in enumerate(report_sections):
            if not section.strip():
                continue
                
            lines = section.strip().split('\n')
            title = lines[0].replace('#', '').strip()
            
            if title:
                st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)
                
                content = '\n'.join(lines[1:]) if len(lines) > 1 else ''
                
                # Enhanced content formatting with proper text styling and staggered animations
                animation_delay = i * 0.2  # Stagger animations by 0.2s per section
                
                if 'kg CO2' in content or 'carbon' in content.lower():
                    st.markdown(f'<div class="highlight-box" style="animation-delay: {animation_delay}s;"><div style="color: #155724 !important; font-weight: 500;">{content}</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="metric-card" style="animation-delay: {animation_delay}s;"><div style="color: #333333 !important; font-weight: 500;">{content}</div></div>', unsafe_allow_html=True)
                
                # Also render the content as markdown for proper formatting
                st.markdown(content)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Download Section with Enhanced Styling
        st.markdown("""
        <div class="download-section">
            <h3>📥 Export Your Analysis</h3>
            <p>Download your comprehensive report and data</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Download Report (MD)",
                st.session_state.report_data,
                "green_wallet_report.md",
                "text/markdown",
                use_container_width=True,
                key="download_md"
            )
        with col2:
            st.download_button(
                "📊 Export Data (JSON)",
                json.dumps({
                    "wallet": wallet_address, 
                    "timestamp": str(Path("outputs/onchain_intelligence_report.md").stat().st_mtime),
                    "analysis_type": "green_wallet_carbon_analysis"
                }, indent=2),
                "green_wallet_data.json",
                "application/json",
                use_container_width=True,
                key="download_json"
            )

with tab2:
    st.markdown("### Carbon Footprint Dashboard")
    
    if st.session_state.analysis_complete and st.session_state.report_data:
        carbon_section = extract_carbon_data(st.session_state.report_data)
        
        if carbon_section and carbon_section.get('total_co2_kg', 0) > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="carbon-metric" style="animation-delay: 0s;">
                    <h3>Total CO2 Emissions</h3>
                    <div class="value">{carbon_section.get('total_co2_kg', 0):.4f}</div>
                    <div class="unit">kg CO2</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="carbon-metric" style="animation-delay: 0.2s;">
                    <h3>Energy Consumption</h3>
                    <div class="value">{carbon_section.get('total_energy_kwh', 0):.4f}</div>
                    <div class="unit">kWh</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="carbon-metric" style="animation-delay: 0.4s;">
                    <h3>Total Transactions</h3>
                    <div class="value">{carbon_section.get('total_transactions', 0):,}</div>
                    <div class="unit">transactions</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="carbon-metric" style="animation-delay: 0.6s;">
                    <h3>Avg per Transaction</h3>
                    <div class="value">{carbon_section.get('avg_per_tx', 0):.6f}</div>
                    <div class="unit">kg CO2</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if carbon_section.get('network_data'):
                    fig_pie = create_animated_network_chart(carbon_section['network_data'])
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                if carbon_section.get('equivalents'):
                    fig_equiv = create_equivalents_chart(carbon_section['equivalents'])
                    st.plotly_chart(fig_equiv, use_container_width=True)
            
            total_co2 = carbon_section.get('total_co2_kg', 0)
            if total_co2 < 0.1:
                st.markdown('<div class="status-alert carbon-low"><strong>✅ Excellent:</strong> Your carbon footprint is very low!</div>', unsafe_allow_html=True)
            elif total_co2 < 1.0:
                st.markdown('<div class="status-alert carbon-medium"><strong>⚠️ Moderate:</strong> Consider L2 migration to reduce emissions.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-alert carbon-high"><strong>🚨 High Impact:</strong> Implement reduction strategies immediately.</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                        border-radius: 15px; padding: 30px; text-align: center; 
                        border: 2px dashed #28a745;">
                <h3 style="color: #28a745;">📊 No Carbon Data Available</h3>
                <p style="color: #6c757d; font-size: 1.1em;">This could mean:</p>
                <ul style="color: #6c757d; text-align: left; max-width: 400px; margin: 0 auto;">
                    <li>No transactions detected on analyzed networks</li>
                    <li>Wallet has minimal on-chain activity</li>
                    <li>Data extraction issue</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                    border-radius: 15px; padding: 30px; text-align: center; 
                    border: 2px dashed #28a745;">
            <h3 style="color: #28a745;">🌱 Ready for Analysis</h3>
            <p style="color: #6c757d; font-size: 1.1em;">Run a wallet analysis to see carbon footprint data</p>
            <p style="color: #6c757d;">Your blockchain activities will be translated into environmental metrics</p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div class='footer'>
    <strong style='color: #22c55e;'>🌱 Green Wallet - Powered by Moralis, Zapper & OpenAI</strong>
    <p style='margin: 0.5rem 0 0 0;'>Sustainable Blockchain Analytics v2.0 - Made with ❤️</p>
</div>
""", unsafe_allow_html=True)