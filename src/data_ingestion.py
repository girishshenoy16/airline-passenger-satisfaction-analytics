"""Data Ingestion Module - Load Airline Passenger Satisfaction dataset."""

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yaml


class SurveyDataIngestor:
    """Handles loading the Airline Passenger Satisfaction dataset."""

    AIRLINE_COLUMN_MAP = {
        "id": "respondent_id",
        "Gender": "gender",
        "Customer Type": "customer_type",
        "Age": "age",
        "Type of Travel": "travel_type",
        "Class": "service_class",
        "satisfaction": "selected_option",
    }

    AGE_GROUP_BINS = [0, 18, 25, 35, 45, 55, 65, 100]
    AGE_GROUP_LABELS = ["Under 18", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"]

    def __init__(self, config_path: str = "config/settings.yaml") -> None:
        """Initialize with configuration file."""
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

    def load_airline_dataset(self, data_dir: str = "data/raw") -> pd.DataFrame:
        """Load and transform the Airline Passenger Satisfaction dataset.

        Args:
            data_dir: Directory containing train.csv and test.csv.

        Returns:
            DataFrame mapped to project's analytical model.
        """
        data_path = Path(data_dir)

        train_file = data_path / "train.csv"
        test_file = data_path / "test.csv"

        dfs = []
        if train_file.exists():
            dfs.append(pd.read_csv(train_file))
        if test_file.exists():
            dfs.append(pd.read_csv(test_file))

        if not dfs:
            raise FileNotFoundError(f"No dataset files found in {data_dir}")

        df = pd.concat(dfs, ignore_index=True)

        df = self._transform_airline_data(df)

        return df

    def _transform_airline_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform Airline dataset to project's analytical model.

        Args:
            df: Raw Airline dataset.

        Returns:
            Transformed DataFrame.
        """
        result = pd.DataFrame()

        result["respondent_id"] = df["id"].apply(lambda x: f"R{str(x).zfill(6)}")

        result["age"] = df["Age"]
        result["age_group"] = pd.cut(
            df["Age"],
            bins=self.AGE_GROUP_BINS,
            labels=self.AGE_GROUP_LABELS,
            right=False,
        ).astype(str)

        result["gender"] = df["Gender"]

        result["region"] = df["Class"].map({
            "Business": "Premium",
            "Eco Plus": "Standard",
            "Eco": "Economy",
        }).fillna("Unknown")

        result["selected_option"] = df["satisfaction"].map({
            "satisfied": "Satisfied",
            "neutral or dissatisfied": "Neutral/Dissatisfied",
        }).fillna("Unknown")

        result["customer_type"] = df["Customer Type"]
        result["travel_type"] = df["Type of Travel"]
        result["service_class"] = df["Class"]
        result["flight_distance"] = df["Flight Distance"]

        service_cols = [
            "Inflight wifi service",
            "Departure/Arrival time convenient",
            "Ease of Online booking",
            "Gate location",
            "Food and drink",
            "Online boarding",
            "Seat comfort",
            "Inflight entertainment",
            "On-board service",
            "Leg room service",
            "Baggage handling",
            "Checkin service",
            "Inflight service",
            "Cleanliness",
        ]
        for col in service_cols:
            clean_name = col.lower().replace(" ", "_").replace("/", "_")
            result[clean_name] = df[col]

        result["departure_delay"] = df["Departure Delay in Minutes"]
        result["arrival_delay"] = df["Arrival Delay in Minutes"]

        return result

    @staticmethod
    def get_config_defaults() -> dict:
        """Return default configuration values."""
        return {
            "data_dir": "data/raw",
        }
