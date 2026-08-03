"""Data Validation Module - Column checks, missing values, duplicates."""

from dataclasses import dataclass
from typing import List, Tuple

import pandas as pd
import yaml


@dataclass
class ValidationResult:
    """Container for data validation results."""

    is_valid: bool
    total_records: int
    missing_counts: dict
    missing_percentage: float
    duplicate_count: int
    duplicate_percentage: float
    errors: List[str]
    warnings: List[str]


class SurveyDataValidator:
    """Validates survey data for required columns, missing values, and duplicates."""

    REQUIRED_COLUMNS = [
        "respondent_id",
        "age_group",
        "gender",
        "region",
        "selected_option",
    ]

    def __init__(self, config_path: str = "config/settings.yaml") -> None:
        """Initialize with configuration thresholds."""
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.thresholds = self.config.get("thresholds", {})
        self.missing_warning = self.thresholds.get("missing_rate_warning", 5)
        self.duplicate_warning = self.thresholds.get("risk_threshold_duplicate_pct", 5)

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """Run full validation on a survey DataFrame.

        Args:
            df: Input survey DataFrame.

        Returns:
            ValidationResult with all validation metrics.
        """
        errors: List[str] = []
        warnings: List[str] = []

        missing_cols = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")
            return ValidationResult(
                is_valid=False,
                total_records=len(df),
                missing_counts={},
                missing_percentage=0.0,
                duplicate_count=0,
                duplicate_percentage=0.0,
                errors=errors,
                warnings=warnings,
            )

        total = len(df)
        missing_counts = df[self.REQUIRED_COLUMNS].isnull().sum().to_dict()
        total_missing = sum(missing_counts.values())
        missing_pct = (total_missing / (total * len(self.REQUIRED_COLUMNS))) * 100

        if missing_pct > self.missing_warning:
            warnings.append(
                f"Missing rate ({missing_pct:.1f}%) exceeds {self.missing_warning}% threshold"
            )

        dup_mask = df.duplicated(subset=["respondent_id"], keep=False)
        dup_count = int(dup_mask.sum())
        dup_pct = (dup_count / total) * 100 if total > 0 else 0.0

        if dup_pct > self.duplicate_warning:
            warnings.append(
                f"Duplicate rate ({dup_pct:.1f}%) exceeds {self.duplicate_warning}% threshold"
            )

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            total_records=total,
            missing_counts=missing_counts,
            missing_percentage=missing_pct,
            duplicate_count=dup_count,
            duplicate_percentage=dup_pct,
            errors=errors,
            warnings=warnings,
        )

    def get_clean_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """Remove duplicates and return clean data with count of removed rows.

        Args:
            df: Input DataFrame.

        Returns:
            Tuple of (cleaned DataFrame, number of rows removed).
        """
        original_len = len(df)
        clean_df = df.drop_duplicates(subset=["respondent_id"], keep="first")
        removed = original_len - len(clean_df)
        return clean_df, removed
