from typing import Dict
import pandas as pd

def calculate_statistics(data: Dict) -> pd.DataFrame:
    """
    Produce statistics from data
    :param data: data from API
    :return:
    """

    df = pd.DataFrame.from_dict(data, orient="columns")

    voltage_stats = df["voltage"].describe()
    current_stats = df["current"].describe()

    # Power and Energy
    df["power"] = df["voltage"] * df["current"]  # Power (P = V * I)
    power_stats = df["power"].describe()
    total_energy = (df["power"].sum() / 1000) * (1 / 60)  # Assuming hourly data -> kWh

    # Correlation
    correlation = df["voltage"].corr(df["current"])

    # Combine into a summary DataFrame
    summary = pd.DataFrame({
        "Metric": ["Mean", "Standard Deviation", "Minimum", "Maximum", "Median", "Total Energy (kWh)", "Correlation (V-I)"],
        "Voltage": [voltage_stats["mean"], voltage_stats["std"], voltage_stats["min"], voltage_stats["max"], voltage_stats["50%"], "-", "-"],
        "Current": [current_stats["mean"], current_stats["std"], current_stats["min"], current_stats["max"], current_stats["50%"], "-", "-"],
        "Power": [power_stats["mean"], power_stats["std"], power_stats["min"], power_stats["max"], power_stats["50%"], total_energy, correlation],
    })
    return summary