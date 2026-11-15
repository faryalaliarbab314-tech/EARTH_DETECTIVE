
import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Earth Detective | Pakistan",
    page_icon="🌍",
    layout="wide"
)

FILE1 = "data/new_data_2000.nc"
FILE2 = "data/new_data_2011.nc"
VARIABLE = "M2T1NXSLV_5_12_4_T2M"

@st.cache_data
def load_data(path):
    with xr.open_dataset(path) as ds:
        return ds[VARIABLE].load().squeeze() - 273.15

try:
    temp1 = load_data(FILE1)
    temp2 = load_data(FILE2)

    if not np.array_equal(temp1.lat.values, temp2.lat.values):
        st.error("Latitude grids do not match.")
        st.stop()

    if not np.array_equal(temp1.lon.values, temp2.lon.values):
        st.error("Longitude grids do not match.")
        st.stop()

except Exception as error:
    st.error(f"Could not load NASA datasets: {error}")
    st.stop()

difference = temp2 - temp1

weights = np.cos(np.deg2rad(temp1.lat))

mean1 = float(temp1.weighted(weights).mean(("lat", "lon")))
mean2 = float(temp2.weighted(weights).mean(("lat", "lon")))
average_change = float(
    difference.weighted(weights).mean(("lat", "lon"))
)

df = difference.to_dataframe(
    name="Change (°C)"
).reset_index()

warmer = int((difference > 0).sum())
cooler = int((difference < 0).sum())
unchanged = int((difference == 0).sum())
total = int(difference.count())

# SIDEBAR
st.sidebar.title("🌍 Earth Detective")
page = st.sidebar.radio(
    "Explore the project",
    [
        "Home",
        "Temperature Maps",
        "Change Detection",
        "Hotspots",
        "Statistics",
        "Conclusion"
    ]
)

# HOME
if page == "Home":

    st.title("🌍 EARTH DETECTIVE")
    st.subheader("Investigating Pakistan's Temperature Patterns")

    st.write("""
    This project investigates how the spatial distribution
    of 2-meter air temperature across the selected Pakistan
    region differs between two periods.
    """)

    st.info("""
    **Research question**

    How did the average 2-meter air temperature distribution
    differ between 2000–2010 and 2011–2020?
    """)

    st.subheader("NASA Dataset Information")

    st.write("""
    - Source: NASA MERRA-2 through Giovanni
    - Variable: 2-meter air temperature (T2M)
    - First period: 2000–2010
    - Second period: 2011–2020
    - Region: 60°E–78°E, 23°N–37°N
    - Grid: 29 × 29 locations
    """)

    st.subheader("Our Investigation")
    st.write("""
    We compare two time-averaged temperature maps,
    calculate their differences, and identify locations
    with the largest positive and negative changes.
    """)

# TEMPERATURE MAPS
elif page == "Temperature Maps":

    st.title("🌡️ Temperature Distribution")

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=[
            "2000–2010 Average",
            "2011–2020 Average"
        ]
    )

    fig.add_trace(
        go.Heatmap(
            x=temp1.lon.values,
            y=temp1.lat.values,
            z=temp1.values,
            colorscale="RdYlBu_r",
            colorbar=dict(title="°C")
        ),
        row=1,
        col=1
    )

    fig.add_trace(
        go.Heatmap(
            x=temp2.lon.values,
            y=temp2.lat.values,
            z=temp2.values,
            colorscale="RdYlBu_r",
            showscale=False
        ),
        row=1,
        col=2
    )

    fig.update_layout(height=600)

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "These are period-average grid maps, not annual temperature maps."
    )

# CHANGE DETECTION
elif page == "Change Detection":

    st.title("🗺️ Temperature Change Detection")

    st.write(
        "Later period (2011–2020) minus earlier period (2000–2010) in °C. "
        "**Red** indicates warming; **Blue** indicates cooling."
    )

    # Add a sidebar or expander control for color scaling to make reds pop
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        scale_mode = st.radio(
            "Color Scale Range", 
            ["Dynamic (Best for contrast)", "Symmetric (Balanced)"],
            index=0
        )

    if scale_mode == "Dynamic (Best for contrast)":
        zmin = float(difference.min())
        zmax = float(difference.max())
        # If dynamic, we don't force zmid=0 so the colors stretch fully across actual values
        zmid = None 
    else:
        limit = float(abs(difference).max())
        zmin = -limit
        zmax = limit
        zmid = 0

    fig = go.Figure(
        go.Heatmap(
            x=difference.lon.values,
            y=difference.lat.values,
            z=difference.values,
            colorscale="RdBu_r",
            zmin=zmin,
            zmax=zmax,
            zmid=zmid,
            colorbar=dict(title="Change (°C)"),
            hovertemplate="Lon: %{x}°E<br>Lat: %{y}°N<br>Change: %{z:+.3f}°C<extra></extra>"
        )
    )

    fig.update_layout(
        title="Temperature Difference: 2011–2020 vs 2000–2010",
        xaxis_title="Longitude (°E)",
        yaxis_title="Latitude (°N)",
        height=650
    )

    st.plotly_chart(fig, width="stretch")

    col1, col2, col3 = st.columns(3)
    col1.metric("Area-Weighted Avg Change", f"{average_change:+.3f} °C")
    col2.metric("Max Warming Cell", f"{float(difference.max()):+.3f} °C")
    col3.metric("Max Cooling Cell", f"{float(difference.min()):+.3f} °C")
    
# HOTSPOTS
elif page == "Hotspots":

    st.title("📍 Temperature Hotspots")

    warming = df.sort_values(
        "Change (°C)", ascending=False
    ).head(10)

    cooling = df.sort_values(
        "Change (°C)", ascending=True
    ).head(10)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Warming Grid Cells")
        st.dataframe(warming, hide_index=True)

    with col2:
        st.subheader("Top 10 Cooling Grid Cells")
        st.dataframe(cooling, hide_index=True)

# STATISTICS
# STATISTICS
elif page == "Statistics":

    st.title("📊 Research Statistics")

    c1, c2, c3 = st.columns(3)

    c1.metric("2000–2010 Mean", f"{mean1:.2f} °C")
    c2.metric("2011–2020 Mean", f"{mean2:.2f} °C")
    c3.metric("Average Difference", f"{average_change:+.3f} °C")

    st.subheader("Grid Cell Distribution")

    p1 = warmer / total * 100
    p2 = cooler / total * 100
    p3 = unchanged / total * 100

    st.write(f"Total valid grid cells: **{total}**")
    st.write(f"Warmer: **{warmer} ({p1:.2f}%)**")
    st.write(f"Cooler: **{cooler} ({p2:.2f}%)**")
    st.write(f"Unchanged: **{unchanged} ({p3:.2f}%)**")

    # Explicitly set colors so they match the temperature theme (Red for warmer, Blue for cooler)
    fig = go.Figure(
        go.Pie(
            labels=["Warmer", "Cooler", "Unchanged"],
            values=[warmer, cooler, unchanged],
            hole=0.35,
            marker=dict(colors=["#d62728", "#1f77b4", "#7f7f7f"]) # Red for warmer, Blue for cooler, Gray for unchanged
        )
    )

    fig.update_layout(title="Distribution of Grid Cell Changes")

    st.plotly_chart(fig, width="stretch")

# CONCLUSION
elif page == "Conclusion":

    st.title("🔎 Research Conclusion")

    st.write(f"""
    The area-weighted average temperature difference
    between the two periods was **{average_change:+.3f} °C**.

    There were **{warmer} warmer grid cells** and
    **{cooler} cooler grid cells** out of {total} valid cells.
    """)

    st.write("""
    The results show that the later period had a lower
    area-weighted average temperature across the selected
    grid compared with the earlier period.
    """)

    st.warning("""
    **Research limitation**

    This study compares two time-averaged maps. It does not
    establish an annual warming or cooling trend, explain
    the causes of temperature differences, or represent
    only locations inside Pakistan's political boundary.
    """)

    st.success("Earth Detective analysis dashboard completed!")
