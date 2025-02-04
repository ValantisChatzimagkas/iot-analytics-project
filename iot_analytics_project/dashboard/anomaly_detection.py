from enum import Enum

import pandas as pd
from adtk.data import validate_series
from adtk.detector import QuantileAD
from pydantic import confloat


class BaseOptions(str, Enum):

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

class AnomalyDetectionMethodOptions(BaseOptions):
    quantile = "quantile"
    value_based = "value_based"




def threshold_anomaly_detection(time_series: pd.Series, low_threshold: float, high_threshold: float):
    """
    Flag anomalies based on high and low thresholds.
    :param time_series: data from API, converted to time_series
    :param low_threshold: values <= this will be flagged as anomalies
    :param high_threshold: values >= this will be flagged as anomalies
    :return: puts True if data point falls in the criteria and false if it does not
    """
    return (time_series < low_threshold) | (time_series > high_threshold)


def adtk_anomaly_detection(time_series: pd.Series, low=0.01, high=0.99):
    """
    Perform anomaly detection using ADTK with the quantile method.
    :param time_series: data from API, converted to time_series
    :param low: smallest quantile
    :param high: biggest quantile
    :return:
    """

    ts_valid = validate_series(time_series)

    # Select anomaly detection method: Quantile
    detector = QuantileAD(low=low, high=high)
    detector.fit(ts_valid)
    anomalies = detector.detect(ts_valid)

    return anomalies


class AnomalyDetectionHandler:

    @staticmethod
    def quantile(time_series: pd.Series,
                 low_threshold: confloat(ge=0.0, le=1.00),
                 high_threshold: confloat(ge=0.0, le=1.00)
                 ):
        """
        This method implements anomaly detection via the quantile method
        :param time_series: time series data for processing
        :param low_threshold: lowest quantile
        :param high_threshold: highest quantile
        :return:
        """
        anomalies = pd.Series([False] * len(time_series), index=time_series.index)  # Initialize as no anomalies
        adtk_anomalies = adtk_anomaly_detection(time_series, low_threshold, high_threshold)
        return anomalies | adtk_anomalies


    @staticmethod
    def value_based(time_series: pd.Series,
                 low_threshold: float,
                 high_threshold: float
                 ):
        """
        This method implements anomaly detection based on high and low thresholds applied on the values of data
        :param time_series: time series data for processing        :param low_threshold:
        :param low_threshold: lowest value that everything below this is an anomaly
        :param high_threshold: highest value that everything above this is an anomaly
        :return:
        """
        anomalies = pd.Series([False] * len(time_series), index=time_series.index)  # Initialize as no anomalies
        adtk_anomalies = threshold_anomaly_detection(time_series, low_threshold, high_threshold)
        return anomalies | adtk_anomalies


anomaly_detection_methods_mapper = {
    AnomalyDetectionMethodOptions.quantile: lambda d,l,h: AnomalyDetectionHandler.quantile(
        time_series=d,
        low_threshold=l,
        high_threshold=h
    ),
    AnomalyDetectionMethodOptions.value_based: lambda d, l, h: AnomalyDetectionHandler.value_based(
        time_series=d,
        low_threshold=l,
        high_threshold=h
    )
}