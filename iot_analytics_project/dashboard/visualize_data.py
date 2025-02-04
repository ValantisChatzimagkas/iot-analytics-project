import time
from typing import Any, Dict, List, Optional
import requests
import streamlit as st
from loguru import logger
from anomaly_detection import AnomalyDetectionMethodOptions
from plots import render_line_chart, render_histogram_chart, detect_and_plot_anomalies
from utils import calculate_statistics

# Constants
# BASE_URL = "http://127.0.0.1:8000"

BASE_URL = "http://api:8000"
DEVICE_ENDPOINT = f"{BASE_URL}/devices"
DATA_ENDPOINT = f"{BASE_URL}/data"

if "show_table" not in st.session_state:
    st.session_state.show_table = False


def toggle_table():
    st.session_state.show_table = not st.session_state.show_table


# Streamlit Page Configuration
st.set_page_config(
    page_title="Device Monitoring Dashboard",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Layout
_, header, _ = st.columns([0.1, 99.8, 0.1])
row_1_col_1, row_1_col_2 = st.columns([50, 50])



def fetch_device_ids() -> Optional[List[str]]:
    """Fetch available device IDs from the API."""
    try:
        response = requests.get(DEVICE_ENDPOINT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch device IDs: {e}")
        return None


@st.cache_data
def fetch_device_data(device_id: str) -> Optional[Dict[str, Any]]:
    """Fetch data for a specific device."""
    try:
        response = requests.get(f"{DATA_ENDPOINT}/{device_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch data for device {device_id}: {e}")
        return None


def main():

    device_ids = fetch_device_ids()

    with st.sidebar:
        st.title("Available Devices")
        device = (
            st.selectbox("Select Device ID", options=device_ids, index=0)
            if device_ids
            else None
        )

    with header:

        if device:
            data, offset = fetch_device_data(device)
            st.header(f"Statistics for device: {device}")
            statistics = calculate_statistics(data)

            st.button("Show/Hide Statistics", on_click=toggle_table)

            # Show or hide the table based on the toggle state
            if st.session_state.show_table:
                st.table(statistics)

        with row_1_col_1:
            st.header("Plots")

        with row_1_col_2:
            st.header("")

        # Render charts
        render_line_chart(data, row_1_col_1,
                          chart_params=dict(title=f"Current for device: {device}", color="yellow", variable='current'))
        render_line_chart(data, row_1_col_2,
                          chart_params=dict(title=f"Voltage for device: {device}", color="orange", variable='voltage'))

        render_histogram_chart(data, row_1_col_1,
                               chart_params=dict(title=f"Histogram for device {device} on electrical current",
                                                 color="yellow", x="current", bin_step=0.0009))

        render_histogram_chart(data, row_1_col_2,
                               chart_params=dict(title=f"Histogram for device {device} on voltage",
                                                 color="orange", x="voltage", bin_step=0.2))

        with row_1_col_1:
            st.header("Anomaly Detection")

            e_current_plot_anomaly_method = st.selectbox("anomaly detection method:",
                                                         options=AnomalyDetectionMethodOptions.list(),
                                                         key="e_current_anomaly_method")
            col1, col2 = st.columns(2)
            with col1:
                e_current_low_thresh = st.number_input(
                    "Low Threshold:", value=0.0, key="e_current_low_threshold"
                )

            with col2:
                e_current_high_thresh = st.number_input(
                    "High Threshold:", value=1.0, key="e_current_high_threshold"
                )

            detect_and_plot_anomalies(
                data=data, container=row_1_col_1,
                chart_params=dict(x="current", quantile=True,
                                  anomaly_method=e_current_plot_anomaly_method,
                                  low=e_current_low_thresh,
                                  high=e_current_high_thresh)
            )
            with row_1_col_2:
                st.header("")
                voltage_plot_anomaly_method = st.selectbox("anomaly detection method:",
                                                           options=AnomalyDetectionMethodOptions.list(),
                                                           key="voltage_anomaly_method")
                col1, col2 = st.columns(2)
                with col1:
                    voltage_low_thresh = st.number_input("Low Threshold: ",value=0.0, key="voltage_low_threshold")
                with col2:
                    voltage_high_thresh = st.number_input("High Threshold: ",value=1.0, key="voltage_high_threshold")
            detect_and_plot_anomalies(
                data=data, container=row_1_col_2,
                chart_params=dict(x="voltage", quantile=True,
                                  anomaly_method=voltage_plot_anomaly_method,
                                  low=voltage_low_thresh, high=voltage_high_thresh
                                  )
            )

        with row_1_col_2:
            for i in range(statistics.shape[1] + 1):
                st.header("")


if __name__ == "__main__":
    main()
