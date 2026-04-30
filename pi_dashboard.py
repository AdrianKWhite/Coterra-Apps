import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# Optional import: pyodbc for Denodo connection
try:
    import pyodbc
    PYODBC_AVAILABLE = True
    PYODBC_ERROR = None
except Exception as e:
    PYODBC_AVAILABLE = False
    PYODBC_ERROR = str(e)

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(page_title="Asset Management Dashboard", layout="wide")
st.title("📊 Asset Management Dashboard")
st.caption("One Source - Real-time asset and equipment visibility from Maximo")

# ============================================================================
# DENODO/ONESOURCE CONNECTION
# ============================================================================
@st.cache_resource
def get_denodo_connection():
    """Establish connection to Denodo/OneSource"""
    if not PYODBC_AVAILABLE:
        st.error(
            f"❌ **pyodbc Module Not Available**\n\n"
            f"Install it with: `pip install pyodbc`\n\n"
            f"Error details: {PYODBC_ERROR}"
        )
        return None
    
    try:
        # Using the OneSource ODBC DSN configured on your machine
        conn = pyodbc.connect('DSN=OneSource ODBC')
        return conn
    except Exception as e:
        st.error(
            f"❌ **Denodo Connection Failed**\n\n"
            f"Error: {str(e)}\n\n"
            f"**Troubleshooting:**\n"
            f"1. Verify ODBC DSN 'OneSource ODBC' exists\n"
            f"2. Check Denodo server is accessible\n"
            f"3. Verify your credentials\n"
            f"4. See ONESOURCE_SETUP.md for full setup guide"
        )
        return None

# ============================================================================
# SAMPLE DATA GENERATION (for demo/development)
# ============================================================================
@st.cache_data
def generate_sample_data():
    """Generate sample Maximo asset data for testing"""
    dates = pd.date_range(start='2026-01-01', end='2026-04-29', freq='D')
    unit_nums = ['379', '484', '386', '10434', '551', '298']
    models = ['Centrifugal Compressor', 'Rotary Screw Compressor', 'Motor Drive Unit', 'Control Module', 'Gas Engine']
    vendors = ['Dresser-Rand', 'Atlas Copco', 'Siemens', 'Ingersoll-Rand', 'GE']
    failure_classes = ['Operating', 'Failed', 'Maintenance', 'Alert', 'Shutdown']
    
    data = []
    for unit in unit_nums:
        for _ in range(20):
            random_date = np.random.choice(dates)
            data.append({
                'asset_unit_num': unit,
                'asset_model_desc': np.random.choice(models),
                'asset_vendor_desc': np.random.choice(vendors),
                'asset_failure_class_desc': np.random.choice(failure_classes),
                'asset_updated_date_time': random_date,
                'asset_purch_price': np.random.uniform(5000, 500000),
                'asset_rpl_cost': np.random.uniform(10000, 750000),
                'asset_leased_flag': np.random.choice([0, 1]),
                'asset_manuf_date': pd.Timestamp(np.random.randint(2010, 2023), 
                                                  np.random.randint(1, 13), 
                                                  np.random.randint(1, 29)),
                'asset_expd_life_yrs': np.random.randint(5, 20),
                'asset_serial_num': f"SN-{np.random.randint(100000, 999999)}"
            })
    
    return pd.DataFrame(data)

# ============================================================================
# DATA FETCHING
# ============================================================================
def fetch_pi_data(query):
    """Fetch data from Denodo using the provided query"""
    conn = get_denodo_connection()
    
    if conn is None:
        # Return sample data if no connection
        st.info("Using sample data. To use live Denodo data, see ONESOURCE_SETUP.md")
        return generate_sample_data()
    
    try:
        df = pd.read_sql(query, conn)
        if len(df) == 0:
            st.warning("Query executed but returned no results. Check your filters or table name.")
        return df
    except Exception as e:
        st.error(f"Query error: {str(e)}\n\nCheck your SQL syntax and table names.")
        st.info("Using sample data instead.")
        return generate_sample_data()

# ============================================================================
# SIDEBAR: FILTERS & SORTING
# ============================================================================
st.sidebar.header("🔧 Filters & Sorting")

# Quick action buttons
st.sidebar.subheader("⚡ Quick Filters")
show_critical_only = st.sidebar.checkbox("🚨 Critical Only", value=False, help="Show only Failed/Alert/Shutdown assets", key="quick_critical")
show_high_value = st.sidebar.checkbox("💰 High Value", value=False, help="Show assets > $100k purchase price", key="quick_high_value")
show_leased_only = st.sidebar.checkbox("🔄 Leased", value=False, help="Show only leased assets", key="quick_leased")

# Search functionality
st.sidebar.subheader("🔍 Search")
search_type = st.sidebar.radio("Search by:", ["Unit Number", "Serial Number", "Model/Vendor"], horizontal=True)
search_term = st.sidebar.text_input(
    "Enter search term",
    placeholder="Type to filter...",
    help="Leave empty to show all"
)

# Advanced filters (collapsible)
with st.sidebar.expander("📊 Date & Time Filters", expanded=True):
    date_range = st.date_input(
        "Last Updated Date Range",
        value=(datetime.now() - timedelta(days=90), datetime.now()),
        key="date_range"
    )
    
    sort_by_date = st.selectbox(
        "Sort by Date",
        ["Recent First", "Oldest First", "No Sort"],
        help="Order results by update date"
    )

with st.sidebar.expander("💰 Cost Filters", expanded=False):
    cost_filter_type = st.radio("Filter by:", ["Purchase Price", "Replacement Cost"], key="cost_type")
    
    # Get max values from sample data for slider range
    sample_df = generate_sample_data()
    if cost_filter_type == "Purchase Price":
        max_cost = sample_df['asset_purch_price'].max() if 'asset_purch_price' in sample_df.columns else 500000
    else:
        max_cost = sample_df['asset_rpl_cost'].max() if 'asset_rpl_cost' in sample_df.columns else 750000
    
    cost_range = st.slider(
        f"${cost_filter_type} Range",
        min_value=0,
        max_value=int(max_cost * 1.5),
        value=(0, int(max_cost)),
        step=1000,
        help="Filter by cost range"
    )
    
    show_high_value_threshold = st.number_input(
        "High-Value Threshold ($)",
        value=100000,
        step=10000,
        help="Define what 'high-value' means"
    )

with st.sidebar.expander("📅 Asset Age Filters", expanded=False):
    filter_by_age = st.checkbox("Filter by Asset Age", value=False, key="filter_by_age")
    age_range = (0, 25)  # Default range
    if filter_by_age:
        age_range = st.slider(
            "Asset Age (years since manufacture)",
            min_value=0,
            max_value=50,
            value=(0, 25),
            step=1
        )
    
    filter_by_remaining_life = st.checkbox("Filter by Expected Remaining Life", value=False, key="filter_by_remaining_life")
    remaining_life_range = (0, 30)  # Default range
    if filter_by_remaining_life:
        remaining_life_range = st.slider(
            "Remaining Life (years)",
            min_value=0,
            max_value=40,
            value=(0, 30),
            step=1
        )

with st.sidebar.expander("📋 Equipment Filters", expanded=True):
    # Unit filter
    unit_filter = st.multiselect(
        "Unit Number(s)",
        options=['All'],
        default=['All'],
        help="Select specific units"
    )
    
    # Model filter
    model_filter = st.multiselect(
        "Equipment Model(s)",
        options=['All'],
        default=['All'],
        help="Filter by equipment type"
    )
    
    # Vendor filter
    vendor_filter = st.multiselect(
        "Vendor(s)",
        options=['All'],
        default=['All'],
        help="Filter by manufacturer/vendor"
    )

with st.sidebar.expander("🏥 Status & Condition Filters", expanded=True):
    status_filter = st.multiselect(
        "Asset Status (Failure Class)",
        options=['All', 'Operating', 'Failed', 'Maintenance', 'Alert', 'Shutdown'],
        default=['All', 'Operating'],
        help="Filter by operational status"
    )
    
    ownership_filter = st.multiselect(
        "Ownership",
        options=['All', 'Owned', 'Leased'],
        default=['All'],
        help="Owned vs Leased assets"
    )

with st.sidebar.expander("🔄 Sorting Options", expanded=False):
    primary_sort = st.selectbox(
        "Primary Sort",
        [
            "Last Updated (Recent)",
            "Last Updated (Oldest)",
            "Purchase Price (High to Low)",
            "Purchase Price (Low to High)",
            "Replacement Cost (High to Low)",
            "Asset Age (Newest)",
            "Asset Age (Oldest)",
            "Unit Number (A-Z)",
            "Status (Critical First)"
        ]
    )

# Data source selection
st.sidebar.divider()
data_source = st.sidebar.radio(
    "Data Source",
    ["Sample Data", "Live Denodo Query"],
    help="Use sample data for demo or connect to live Denodo"
)

# Show pyodbc status
if not PYODBC_AVAILABLE:
    st.sidebar.warning(
        f"⚠️ **pyodbc not found**\n\n"
        f"Error: {PYODBC_ERROR}\n\n"
        f"**Workaround:** You can still enter SQL queries below and copy them to run manually, or install pyodbc:\n\n"
        f"`pip install pyodbc`"
    )

# Custom query (if Live Denodo selected)
if data_source == "Live Denodo Query":
    custom_query = st.sidebar.text_area(
        "Custom Denodo SQL Query",
        value="""-- One Source mxm_asset table query
-- Shows assets updated in last 90 days
SELECT * FROM mxm_asset 
WHERE asset_updated_date_time >= CURRENT_DATE - INTERVAL '90' DAY
ORDER BY asset_updated_date_time DESC
LIMIT 50000""",
        height=120,
        help="Tip: Check SCHEMA_DISCOVERY.md for available columns"
    )
else:
    custom_query = None

# ============================================================================
# LOAD DATA
# ============================================================================
if data_source == "Sample Data":
    df = generate_sample_data()
else:
    if custom_query:
        df = fetch_pi_data(custom_query)
    else:
        df = generate_sample_data()

# Convert date column to datetime if needed
if 'asset_updated_date_time' in df.columns:
    df['asset_updated_date_time'] = pd.to_datetime(df['asset_updated_date_time'])

# Calculate asset age
if 'asset_manuf_date' in df.columns:
    df['asset_age_years'] = (datetime.now() - pd.to_datetime(df['asset_manuf_date'])).dt.days / 365.25

# Calculate remaining life
if 'asset_age_years' in df.columns and 'asset_expd_life_yrs' in df.columns:
    df['remaining_life_years'] = df['asset_expd_life_yrs'] - df['asset_age_years']

# ============================================================================
# APPLY FILTERS
# ============================================================================
if df is not None and len(df) > 0:
    # Date filter
    if 'asset_updated_date_time' in df.columns:
        df = df[(df['asset_updated_date_time'].dt.date >= date_range[0]) & 
                (df['asset_updated_date_time'].dt.date <= date_range[1])]
    
    # Quick filter: Critical assets only
    if show_critical_only:
        df = df[df['asset_failure_class_desc'].isin(['Failed', 'Alert', 'Shutdown'])]
    
    # Quick filter: High-value assets only
    if show_high_value:
        df = df[df['asset_purch_price'] >= show_high_value_threshold]
    
    # Quick filter: Leased only
    if show_leased_only:
        df = df[df['asset_leased_flag'] == 1]
    
    # Search filter
    if search_term:
        search_term = search_term.lower()
        if search_type == "Unit Number":
            df = df[df['asset_unit_num'].astype(str).str.lower().str.contains(search_term, na=False)]
        elif search_type == "Serial Number":
            df = df[df['asset_serial_num'].astype(str).str.lower().str.contains(search_term, na=False)]
        elif search_type == "Model/Vendor":
            df = df[(df['asset_model_desc'].astype(str).str.lower().str.contains(search_term, na=False)) |
                    (df['asset_vendor_desc'].astype(str).str.lower().str.contains(search_term, na=False))]
    
    # Cost range filter
    if cost_filter_type == "Purchase Price":
        df = df[(df['asset_purch_price'] >= cost_range[0]) & (df['asset_purch_price'] <= cost_range[1])]
    else:
        df = df[(df['asset_rpl_cost'] >= cost_range[0]) & (df['asset_rpl_cost'] <= cost_range[1])]
    
    # Asset age filter
    if filter_by_age and 'asset_age_years' in df.columns:
        df = df[(df['asset_age_years'] >= age_range[0]) & (df['asset_age_years'] <= age_range[1])]
    
    # Remaining life filter
    if filter_by_remaining_life and 'remaining_life_years' in df.columns:
        df = df[(df['remaining_life_years'] >= remaining_life_range[0]) & (df['remaining_life_years'] <= remaining_life_range[1])]
    
    # Unit filter
    if 'asset_unit_num' in df.columns and 'All' not in unit_filter:
        df = df[df['asset_unit_num'].isin(unit_filter)]
    
    # Model filter
    if 'asset_model_desc' in df.columns and 'All' not in model_filter:
        df = df[df['asset_model_desc'].isin(model_filter)]
    
    # Vendor filter
    if 'asset_vendor_desc' in df.columns and 'All' not in vendor_filter:
        df = df[df['asset_vendor_desc'].isin(vendor_filter)]
    
    # Status filter
    if 'asset_failure_class_desc' in df.columns and 'All' not in status_filter:
        df = df[df['asset_failure_class_desc'].isin(status_filter)]
    
    # Ownership filter
    if 'asset_leased_flag' in df.columns and 'All' not in ownership_filter:
        if 'Owned' in ownership_filter and 'Leased' not in ownership_filter:
            df = df[df['asset_leased_flag'] == 0]
        elif 'Leased' in ownership_filter and 'Owned' not in ownership_filter:
            df = df[df['asset_leased_flag'] == 1]
    
    # Apply sorting
    if primary_sort == "Last Updated (Recent)":
        df = df.sort_values('asset_updated_date_time', ascending=False)
    elif primary_sort == "Last Updated (Oldest)":
        df = df.sort_values('asset_updated_date_time', ascending=True)
    elif primary_sort == "Purchase Price (High to Low)":
        df = df.sort_values('asset_purch_price', ascending=False)
    elif primary_sort == "Purchase Price (Low to High)":
        df = df.sort_values('asset_purch_price', ascending=True)
    elif primary_sort == "Replacement Cost (High to Low)":
        df = df.sort_values('asset_rpl_cost', ascending=False)
    elif primary_sort == "Asset Age (Newest)":
        df = df.sort_values('asset_age_years', ascending=True)
    elif primary_sort == "Asset Age (Oldest)":
        df = df.sort_values('asset_age_years', ascending=False)
    elif primary_sort == "Unit Number (A-Z)":
        df = df.sort_values('asset_unit_num', ascending=True)
    elif primary_sort == "Status (Critical First)":
        status_priority = {'Failed': 0, 'Alert': 1, 'Shutdown': 2, 'Maintenance': 3, 'Operating': 4}
        df['status_priority'] = df['asset_failure_class_desc'].map(status_priority).fillna(5)
        df = df.sort_values('status_priority')
        df = df.drop('status_priority', axis=1)

# ============================================================================
# TABS FOR DIFFERENT VIEWS
# ============================================================================
# Show filter status and results count
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    active_filters = []
    if show_critical_only:
        active_filters.append("🚨 Critical Only")
    if show_high_value:
        active_filters.append(f"💰 High Value (>${show_high_value_threshold:,})")
    if show_leased_only:
        active_filters.append("🔄 Leased")
    if search_term:
        active_filters.append(f"🔍 {search_type}: '{search_term}'")
    
    if active_filters:
        st.info(f"**Active Filters:** {' | '.join(active_filters)}")

with col2:
    st.metric("Results", len(df))

with col3:
    if len(df) > 0:
        st.metric("Total Value", f"${df['asset_purch_price'].sum():,.0f}" if 'asset_purch_price' in df.columns else "N/A")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["Asset Overview", "Equipment Status", "Financial Analysis", "Maintenance History"])

# ============================================================================
# TAB 1: ASSET OVERVIEW
# ============================================================================
with tab1:
    st.subheader("Asset Inventory Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Assets", len(df))
    
    with col2:
        if 'asset_leased_flag' in df.columns:
            leased_count = len(df[df['asset_leased_flag'] == 1])
            st.metric("Leased Assets", leased_count)
    
    with col3:
        if 'asset_leased_flag' in df.columns:
            owned_count = len(df[df['asset_leased_flag'] == 0])
            st.metric("Owned Assets", owned_count)
    
    with col4:
        if 'asset_purch_price' in df.columns:
            total_value = df['asset_purch_price'].sum()
            st.metric("Total Asset Value", f"${total_value:,.0f}")
    
    # Owned vs Leased Comparison
    if 'asset_leased_flag' in df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            owned_data = df[df['asset_leased_flag'] == 0]
            leased_data = df[df['asset_leased_flag'] == 1]
            
            comparison_data = pd.DataFrame({
                'Type': ['Owned', 'Leased'],
                'Count': [len(owned_data), len(leased_data)],
                'Avg Value': [
                    owned_data['asset_purch_price'].mean() if len(owned_data) > 0 else 0,
                    leased_data['asset_purch_price'].mean() if len(leased_data) > 0 else 0
                ]
            })
            
            fig_comparison = px.bar(
                comparison_data,
                x='Type',
                y=['Count', 'Avg Value'],
                title='Owned vs Leased Comparison',
                barmode='group',
                labels={'value': 'Count / Avg Value ($)'}
            )
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        with col2:
            # Asset age comparison
            if 'asset_age_years' in df.columns:
                age_comparison = pd.DataFrame({
                    'Ownership': [],
                    'Avg Age (years)': [],
                    'Avg Remaining Life': []
                })
                
                owned_age = owned_data['asset_age_years'].mean()
                leased_age = leased_data['asset_age_years'].mean()
                owned_remaining = owned_data['remaining_life_years'].mean() if 'remaining_life_years' in df.columns else 0
                leased_remaining = leased_data['remaining_life_years'].mean() if 'remaining_life_years' in df.columns else 0
                
                age_comparison = pd.DataFrame({
                    'Ownership': ['Owned', 'Leased'],
                    'Avg Age': [owned_age, leased_age]
                })
                
                fig_age_comp = px.bar(
                    age_comparison,
                    x='Ownership',
                    y='Avg Age',
                    title='Average Asset Age Comparison',
                    labels={'Avg Age': 'Age (years)'},
                    color='Ownership',
                    color_discrete_map={'Owned': 'steelblue', 'Leased': 'coral'}
                )
                st.plotly_chart(fig_age_comp, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Assets by model
        if 'asset_model_desc' in df.columns:
            model_counts = df['asset_model_desc'].value_counts().head(10).reset_index()
            model_counts.columns = ['Model', 'Count']
            fig_model = px.bar(
                model_counts,
                x='Model',
                y='Count',
                title='Asset Count by Equipment Model (Top 10)',
                labels={'Count': 'Number of Assets'},
                color='Count',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig_model, use_container_width=True)
    
    with col2:
        # Assets by vendor
        if 'asset_vendor_desc' in df.columns:
            vendor_counts = df['asset_vendor_desc'].value_counts().head(10).reset_index()
            vendor_counts.columns = ['Vendor', 'Count']
            fig_vendor = px.bar(
                vendor_counts,
                x='Vendor',
                y='Count',
                title='Asset Count by Vendor (Top 10)',
                labels={'Count': 'Number of Assets'},
                color='Count',
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig_vendor, use_container_width=True)

# ============================================================================
# TAB 2: EQUIPMENT STATUS
# ============================================================================
with tab2:
    st.subheader("Equipment Status & Health")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Status breakdown (pie chart)
        if 'asset_failure_class_desc' in df.columns:
            status_counts = df['asset_failure_class_desc'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            fig_status_pie = px.pie(
                status_counts,
                names='Status',
                values='Count',
                title='Asset Status Distribution',
                color_discrete_map={
                    'Operating': 'green',
                    'Failed': 'red',
                    'Maintenance': 'orange',
                    'Alert': 'gold',
                    'Shutdown': 'darkred'
                }
            )
            st.plotly_chart(fig_status_pie, use_container_width=True)
    
    with col2:
        # Asset condition/age indicators
        st.subheader("⏳ Asset Condition by Age")
        if 'asset_age_years' in df.columns:
            age_condition = []
            if len(df) > 0:
                age_condition.append(f"🟢 New (0-5 yrs): {len(df[df['asset_age_years'] <= 5])} assets")
                age_condition.append(f"🟡 Mid-Life (5-15 yrs): {len(df[(df['asset_age_years'] > 5) & (df['asset_age_years'] <= 15)])} assets")
                age_condition.append(f"🔴 Aging (15+ yrs): {len(df[df['asset_age_years'] > 15])} assets")
            
            for condition in age_condition:
                st.write(condition)
    
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        # Critical assets table
        if 'asset_failure_class_desc' in df.columns:
            critical = df[df['asset_failure_class_desc'].isin(['Failed', 'Alert', 'Shutdown'])]
            st.subheader("⚠️ Critical & Alert Assets")
            if len(critical) > 0:
                display_cols = ['asset_unit_num', 'asset_model_desc', 'asset_failure_class_desc', 'asset_updated_date_time']
                display_cols = [col for col in display_cols if col in critical.columns]
                st.dataframe(critical[display_cols].head(10), use_container_width=True)
            else:
                st.success("✅ No critical or alert assets")
    
    with col2:
        # Aging assets alert
        if 'asset_age_years' in df.columns:
            aging = df[df['asset_age_years'] > 15]
            st.subheader("📅 Aging Assets (15+ years)")
            if len(aging) > 0:
                display_cols = ['asset_unit_num', 'asset_model_desc', 'asset_age_years', 'remaining_life_years'] if 'remaining_life_years' in df.columns else ['asset_unit_num', 'asset_model_desc', 'asset_age_years']
                display_cols = [col for col in display_cols if col in aging.columns]
                st.dataframe(aging[display_cols].head(10), use_container_width=True)
            else:
                st.success("✅ No aging assets")
    
    # Status timeline
    if 'asset_updated_date_time' in df.columns and 'asset_failure_class_desc' in df.columns:
        status_timeline = df.groupby([pd.Grouper(key='asset_updated_date_time', freq='D'), 'asset_failure_class_desc']).size().reset_index(name='Count')
        fig_timeline = px.area(
            status_timeline,
            x='asset_updated_date_time',
            y='Count',
            color='asset_failure_class_desc',
            title='Asset Status Changes Over Time',
            labels={'asset_updated_date_time': 'Date', 'Count': 'Number of Assets'},
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

# ============================================================================
# TAB 3: FINANCIAL ANALYSIS
# ============================================================================
with tab3:
    st.subheader("Asset Financial Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Purchase price vs replacement cost
        if 'asset_purch_price' in df.columns and 'asset_rpl_cost' in df.columns:
            financial = df[['asset_unit_num', 'asset_purch_price', 'asset_rpl_cost']].dropna()
            if len(financial) > 0:
                financial_summary = financial.sum()
                st.metric("Total Purchase Value", f"${financial_summary['asset_purch_price']:,.0f}")
                st.metric("Total Replacement Cost", f"${financial_summary['asset_rpl_cost']:,.0f}")
    
    with col2:
        # Cost by ownership
        if 'asset_leased_flag' in df.columns and 'asset_purch_price' in df.columns:
            cost_by_ownership = df.groupby(df['asset_leased_flag'].map({0: 'Owned', 1: 'Leased'}))['asset_purch_price'].sum().reset_index()
            cost_by_ownership.columns = ['Ownership', 'Total Value']
            fig_ownership_cost = px.pie(
                cost_by_ownership,
                names='Ownership',
                values='Total Value',
                title='Asset Value by Ownership Type',
                color_discrete_map={'Owned': 'steelblue', 'Leased': 'coral'}
            )
            st.plotly_chart(fig_ownership_cost, use_container_width=True)
    
    # Cost by model
    if 'asset_model_desc' in df.columns and 'asset_purch_price' in df.columns:
        cost_by_model = df.groupby('asset_model_desc')['asset_purch_price'].sum().sort_values(ascending=False).head(10).reset_index()
        cost_by_model.columns = ['Model', 'Total Value']
        fig_model_cost = px.bar(
            cost_by_model,
            x='Model',
            y='Total Value',
            title='Total Purchase Value by Equipment Model (Top 10)',
            labels={'Total Value': 'Purchase Price ($)'},
            color='Total Value',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_model_cost, use_container_width=True)

# ============================================================================
# TAB 4: MAINTENANCE HISTORY
# ============================================================================
with tab4:
    st.subheader("Asset Maintenance & Updates")
    
    # Assets by age
    if 'asset_manuf_date' in df.columns:
        df['asset_age_years'] = (datetime.now() - pd.to_datetime(df['asset_manuf_date'])).dt.days / 365.25
        age_groups = pd.cut(df['asset_age_years'], bins=[0, 5, 10, 15, 20, 50], labels=['0-5 years', '5-10 years', '10-15 years', '15-20 years', '20+ years'])
        age_distribution = age_groups.value_counts().sort_index().reset_index()
        age_distribution.columns = ['Age Group', 'Count']
        
        fig_age = px.bar(
            age_distribution,
            x='Age Group',
            y='Count',
            title='Asset Age Distribution',
            labels={'Count': 'Number of Assets'},
            color='Count',
            color_continuous_scale='Oranges'
        )
        st.plotly_chart(fig_age, use_container_width=True)
    
    # Recent updates
    if 'asset_updated_date_time' in df.columns:
        recent = df.nlargest(20, 'asset_updated_date_time')
        st.subheader("Recently Updated Assets")
        display_cols = ['asset_unit_num', 'asset_model_desc', 'asset_failure_class_desc', 'asset_updated_date_time']
        display_cols = [col for col in display_cols if col in recent.columns]
        st.dataframe(recent[display_cols], use_container_width=True)

# ============================================================================
# FOOTER: RAW DATA VIEW
# ============================================================================
st.divider()
st.subheader("📋 Data Explorer")

if st.checkbox("Show raw filtered data", key="show_raw_data"):
    st.dataframe(df, use_container_width=True)

if st.checkbox("Show available columns", key="show_columns"):
    st.subheader("Column Names & Types")
    st.write(df.dtypes)
    st.caption(f"Total columns: {len(df.columns)}")

# Download button
csv = df.to_csv(index=False)
st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name=f"asset_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv"
)

# ============================================================================
# DENODO/ONESOURCE CONNECTION
# ============================================================================
@st.cache_resource
def get_denodo_connection():
    """Establish connection to Denodo/OneSource"""
    if not PYODBC_AVAILABLE:
        st.error(
            f"❌ **pyodbc Module Not Available**\n\n"
            f"Install it with: `pip install pyodbc`\n\n"
            f"Error details: {PYODBC_ERROR}"
        )
        return None
    
    try:
        # Using the OneSource ODBC DSN configured on your machine
        conn = pyodbc.connect('DSN=OneSource ODBC')
        return conn
    except Exception as e:
        st.error(
            f"❌ **Denodo Connection Failed**\n\n"
            f"Error: {str(e)}\n\n"
            f"**Troubleshooting:**\n"
            f"1. Verify ODBC DSN 'OneSource ODBC' exists\n"
            f"2. Check Denodo server is accessible\n"
            f"3. Verify your credentials\n"
            f"4. See ONESOURCE_SETUP.md for full setup guide"
        )
        return None

# ============================================================================
# SAMPLE DATA GENERATION (for demo/development)
# ============================================================================
@st.cache_data
def generate_sample_data():
    """Generate sample PI data for testing"""
    dates = pd.date_range(start='2026-01-01', end='2026-04-29', freq='D')
    wells = ['Well-A', 'Well-B', 'Well-C', 'Well-D', 'Well-E']
    areas = ['Area-North', 'Area-Central', 'Area-South']
    
    data = []
    for well in wells:
        area = areas[np.random.randint(0, len(areas))]
        for date in dates:
            data.append({
                'date': date,
                'well_name': well,
                'area': area,
                'production_rate': np.random.uniform(100, 500),
                'pressure': np.random.uniform(2000, 3500),
                'temperature': np.random.uniform(80, 120),
                'compression_run_time': np.random.uniform(0, 24),
                'downtime_hours': np.random.uniform(0, 8),
                'status': np.random.choice(['Running', 'Maintenance', 'Idle']),
                'cumulative_production': np.random.uniform(10000, 50000)
            })
    
    return pd.DataFrame(data)

# ============================================================================
# DATA FETCHING
# ============================================================================
def fetch_pi_data(query):
    """Fetch data from Denodo using the provided query"""
    conn = get_denodo_connection()
    
    if conn is None:
        # Return sample data if no connection
        st.info("Using sample data. To use live Denodo data, see ONESOURCE_SETUP.md")
        return generate_sample_data()
    
    try:
        df = pd.read_sql(query, conn)
        if len(df) == 0:
            st.warning("Query executed but returned no results. Check your filters or table name.")
        return df
    except Exception as e:
        st.error(f"Query error: {str(e)}\n\nCheck your SQL syntax and table names.")
        st.info("Using sample data instead.")
        return generate_sample_data()

# ============================================================================
# DISPLAY RESULTS
# ============================================================================


