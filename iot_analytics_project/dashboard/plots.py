from typing import Dict, Any
import pandas as pd
import plotly.express as px
import numpy as np
from scipy.stats import gaussian_kde
import plotly.graph_objs as go
from anomaly_detection import anomaly_detection_methods_mapper


def render_line_chart(data: Dict[str, Any], container: Any, chart_params: Dict):
    """
    Produce and render line chart plot on UI
    :param data: data fetched by the API from a device
    :param container: container in UI that this plot will be placed, e.g. row 1 column 1
    :param chart_params: dictionary containing parameters that specify, color, column from data and other stuff,
        e.g. chart_params: {
            "color":"yellow",
            "title":"Current for device: 12as-asda13",
            "variable":"current"
        }
    :return:
    """
    if data:
        df = pd.DataFrame.from_dict(data, orient="columns")

        fig = px.line(
            df,
            x="timestamp",
            y=chart_params["variable"],
            title=chart_params["title"],
            color_discrete_sequence=[chart_params["color"]],
        )


        fig.update_layout(
            title=dict(
                text=chart_params["title"],
                x=0,
                font=dict(size=16, family="Arial"),
            ),
            xaxis_title="Timestamp",
            yaxis_title=chart_params["variable"].capitalize(),
            template="plotly_white",
            width=700,
            height=400,
        )

        container.plotly_chart(fig, use_container_width=True)
    else:
        container.write("No data available for this device.")


def render_histogram_chart(data: dict, container, chart_params: dict):
    """
    Produce and render histogram plot on UI
    :param data: data fetched by the API from a device
    :param container: container in UI that this plot will be placed, e.g. row 1 column 1
    :param chart_params: dictionary containing parameters that specify, color, column from data and other stuff,
        e.g. chart_params: {
            "color":"yellow",
            "title":"Current for device: 12as-asda13",
            "variable":"current"
        }
    :return:
    """

    if not data:
        container.write("No data available for this device.")
        return

    df = pd.DataFrame.from_dict(data, orient="columns")

    if chart_params["x"] not in df.columns:
        container.write(f"Column '{chart_params['x']}' not found in the data.")
        return

    x_data = df[chart_params["x"]].dropna()

    num_bins = chart_params.get("bins", 20)

    hist_values, bin_edges = np.histogram(x_data, bins=num_bins, density=False)  # Frequency histogram


    kde = gaussian_kde(x_data, bw_method='scott')  # Scott's rule for bandwidth
    kde_x = np.linspace(min(x_data), max(x_data), 200)  # Generate smooth x-values for KDE
    kde_y = kde(kde_x) * len(x_data) * np.diff(bin_edges).mean()  # Scale KDE to match histogram


    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=bin_edges[:-1],  # Start of each bin
        y=hist_values,  # Frequency count
        marker=dict(color=chart_params["color"]),
        name="Histogram",
        opacity=0.6
    ))

    # Add KDE curve
    fig.add_trace(go.Scatter(
        x=kde_x,
        y=kde_y,
        mode='lines',
        line=dict(color='red', width=2),
        name="KDE Curve"
    ))

    fig.update_layout(
        title=chart_params["title"],
        xaxis_title=chart_params["x"],
        yaxis_title="Frequency",
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)',
        title_x=0,
        title_font=dict(size=16)
    )

    container.plotly_chart(fig, use_container_width=True)

def detect_and_plot_anomalies(data: Dict[str, Any], container, chart_params: Dict):
    """
    Detect anomalies in a time series using ADTK or thresholds and plot them in a Streamlit app.
    :param data: data fetched by the API from a device
    :param container: container in UI that this plot will be placed, e.g. row 1 column 1
    :param chart_params: dictionary containing parameters that specify, color, column from data and other stuff,
        e.g. chart_params: {
            "color":"yellow",
            "title":"Current for device: 12as-asda13",
            "variable":"current"
        }
    :return:
    """

    df = pd.DataFrame.from_dict(data, orient="columns")

    # Ensure required columns exist
    if "timestamp" not in df.columns or chart_params["x"] not in df.columns:
        container.write(f"Missing required columns: 'timestamp' or '{chart_params['x']}'")
        return

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)

    # Extract the selected column as a Series
    time_series = df[chart_params["x"]]

    if time_series.empty:
        container.write("No data available for anomaly detection.")
        return

    # Run anomaly detection method
    low = chart_params.get("low", 0.01)  # Default to 0.01 if not specified
    high = chart_params.get("high", 0.99)  # Default to 0.99 if not specified
    anomalies = anomaly_detection_methods_mapper[chart_params['anomaly_method']](time_series, low, high)

    fig = go.Figure()

    # Plot normal points (blue)
    fig.add_trace(go.Scatter(
        x=time_series.index[~anomalies],  # Normal points
        y=time_series[~anomalies],
        mode="markers",
        name="Normal Points",
        marker=dict(color="blue", size=6)
    ))

    # Plot anomalies (red)
    if anomalies.any():
        fig.add_trace(go.Scatter(
            x=time_series.index[anomalies],  # Anomaly points
            y=time_series[anomalies],
            mode="markers",
            name="Anomalies",
            marker=dict(color="red", size=8, symbol="x")
        ))

    fig.update_layout(
        title=f"Anomaly Detection for {chart_params['x']}",
        xaxis_title="Time",
        yaxis_title="Value",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )

    # Display the plot in Streamlit
    container.plotly_chart(fig, use_container_width=True)