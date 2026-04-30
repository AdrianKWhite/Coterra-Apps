# PI Database Dashboard - Streamlit Application

A comprehensive Streamlit dashboard for visualizing and analyzing PI database data from One Source (Denodo).

## Features

✅ **Multiple Data Types** - Switch between Production Data, Equipment Readings, Downtime Events, and System Health  
✅ **Dynamic Filtering** - Filter by date range, well name, area, status, and compression run time  
✅ **Rich Visualizations**:
   - Line charts for time series trends
   - Bar charts for well/area comparisons
   - Gauges for current metrics
   - Heatmaps for pattern analysis
   - Health indicators with color coding

✅ **Health Status Indicators** - Color-coded compression run time (Green = Healthy, Yellow = Monitor, Red = Critical)  
✅ **Live Denodo Connection** - Query live PI data or use sample data for development  
✅ **Data Export** - Download filtered data as CSV  

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure OneSource ODBC Connection

1. Ensure you have a Denodo ODBC driver installed
2. Configure an ODBC DSN named **"OneSource ODBC"** pointing to your Denodo instance
   - If using a different DSN name, update `DEFAULT_DSN = "OneSource ODBC"` in `pi_dashboard.py`

### 3. Run the Dashboard

```bash
streamlit run pi_dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Usage

### Sidebar Filters

- **Date Range**: Select historical period for analysis
- **Data Type**: Choose which data metrics to focus on
- **Well Name(s)**: Filter by specific wells (multi-select available)
- **Area(s)**: Filter by geographic area (North, Central, South)
- **Status**: Filter by operational status (Running, Maintenance, Idle)
- **Compression Run Time - Healthy Threshold**: Set the hours considered "healthy" for run time
- **Data Source**: Choose between Sample Data (demo) or Live Denodo Query

### Tabs

1. **Production Data**
   - Average production rate over time (line chart)
   - Production comparison by well (bar chart)
   - Cumulative production heatmap

2. **Equipment Readings**
   - Gauge charts for Pressure, Temperature, and Compression Run Time
   - Trend charts for Pressure and Temperature

3. **Downtime Events**
   - Total downtime by well (bar chart)
   - Cumulative downtime trend (area chart)
   - Detailed downtime events table

4. **System Health**
   - Health status by well with color coding
   - Status snapshot metrics (Running, Maintenance, Idle)
   - Area-level health analysis (Run Time vs Downtime scatter)

## Sample Data

When using "Sample Data" mode, the dashboard generates 120 days of synthetic data across 5 wells in 3 areas. This is useful for:
- Testing dashboard features
- Development without live database access
- Understanding data structure and flows

## Connecting to Live Denodo Data

### One Source mxm_asset Table
The dashboard is configured to query the **mxm_asset** table from your One Source Denodo instance.

**Shared Query URL:**
```
https://onesource-marketplace.coterra.com:9090/denodo-data-catalog/#shared-query/1cf3742cba3799b32f1469483ad7cfa01cf1e977aad0baaa9fde939d07e0ecdd02a0d0bfffc408d2f27985d246a454f024ccfa5072f764218285fb7fe83bc9f9
```

### Setup Steps

1. **Ensure ODBC DSN is Configured**
   - Create a Denodo ODBC DSN named "OneSource ODBC" on your machine
   - Point it to: `onesource-marketplace.coterra.com:9090`
   - Use your Denodo credentials

2. **Test Connection in Dashboard**
   - Select "Live Denodo Query" in the Data Source filter
   - The default query will fetch from `mxm_asset` table
   - If connection fails, verify ODBC configuration and credentials

3. **Modify Query** (Optional)
   - Edit the SQL in the "Custom Denodo SQL Query" text area
   - Adjust date ranges, add filters, or select specific columns
   - Examples:
     ```sql
     -- Get data for last 90 days
     SELECT * FROM mxm_asset 
     WHERE create_date >= CURRENT_DATE - INTERVAL '90' DAY
     
     -- Filter by specific asset type
     SELECT * FROM mxm_asset 
     WHERE asset_type = 'Compressor'
     AND create_date >= CURRENT_DATE - INTERVAL '30' DAY
     ```

## Customization

### Modify Data Source Query
Edit the query in the sidebar under "Custom Denodo SQL Query" to pull different data or columns

### Add New Metrics
1. Add columns to your SQL query or sample data
2. Create new visualizations in the relevant tab using Plotly
3. Example: `st.plotly_chart(px.line(data, x='date', y='new_metric'))`

### Adjust Health Thresholds
- Use the "Compression Run Time - Healthy Threshold" slider to adjust what's considered healthy
- Modify color thresholds in the gauge charts (search for `'steps'` in the code)

### Adjust Date Ranges
Modify the default date range in the sidebar:
```python
date_range = st.sidebar.date_input(
    "Date Range",
    value=(datetime.now() - timedelta(days=90), datetime.now()),
)
```

## Troubleshooting

**"Connection error" with Live Denodo**
- Verify your ODBC DSN is configured correctly
- Check that your Denodo instance is accessible
- Ensure credentials are stored in ODBC configuration
- Fall back to "Sample Data" mode for testing

**Missing pyodbc module**
- `pip install pyodbc`
- If installation fails, the dashboard will fall back to sample data automatically

**Slow queries**
- Add date filters to your Denodo query to reduce data volume
- Use LIMIT clause to restrict result set
- Consider creating indexed views in Denodo

## File Structure

```
Repos/
├── pi_dashboard.py          # Main Streamlit application
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── app.py                  # Original dashboard (separate)
└── Teams Report.py         # Teams integration utilities
```

## Future Enhancements

Potential features to add:
- Real-time alerts for critical events
- Trend analysis and forecasting
- Multi-facility comparison
- Export reports to PDF
- Integration with Teams notifications
- Custom dashboard configurations saved to database

## Support

For issues or questions:
1. Check the Denodo/OneSource documentation
2. Review the Streamlit documentation: https://docs.streamlit.io
3. Verify your data schema matches the columns referenced in the dashboard

---

**Last Updated**: April 2026  
**Dashboard Version**: 1.0
