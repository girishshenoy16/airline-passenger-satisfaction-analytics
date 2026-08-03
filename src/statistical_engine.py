"""Statistical Engine Module - Chi-Square, Cramér's V, CI, and MoE calculations."""

from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd
import yaml
from scipy import stats


@dataclass
class ChiSquareResult:
    """Container for Chi-Square test results."""

    chi2: float
    p_value: float
    degrees_of_freedom: int
    cramers_v: float
    is_significant: bool


@dataclass
class ConfidenceInterval:
    """Container for confidence interval results."""

    option: str
    proportion: float
    ci_lower: float
    ci_upper: float
    margin_of_error: float
    sample_size: int


class StatisticalEngine:
    """Performs statistical tests and computes confidence intervals."""

    def __init__(self, config_path: str = "config/settings.yaml") -> None:
        """Initialize with statistical configuration."""
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        stats_config = self.config.get("statistics", {})
        self.confidence_level = stats_config.get("confidence_level", 0.95)
        self.z_score = stats_config.get("z_score", 1.96)

    def chi_square_test(
        self, df: pd.DataFrame, col1: str, col2: str
    ) -> ChiSquareResult:
        """Perform Chi-Square test of independence between two categorical variables.

        Args:
            df: Input DataFrame.
            col1: First categorical column.
            col2: Second categorical column.

        Returns:
            ChiSquareResult with test statistics.
        """
        contingency = pd.crosstab(df[col1], df[col2])

        chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

        n = contingency.sum().sum()
        min_dim = min(contingency.shape) - 1
        cramers_v = np.sqrt(chi2 / (n * min_dim)) if (n * min_dim) > 0 else 0.0

        significance = self.config.get("thresholds", {}).get(
            "chi_square_significance", 0.05
        )

        return ChiSquareResult(
            chi2=round(chi2, 4),
            p_value=round(p_value, 6),
            degrees_of_freedom=dof,
            cramers_v=round(cramers_v, 4),
            is_significant=p_value < significance,
        )

    def compute_confidence_intervals(
        self, df: pd.DataFrame
    ) -> list[ConfidenceInterval]:
        """Compute 95% confidence intervals for each option's proportion.

        Args:
            df: DataFrame with 'selected_option' column.

        Returns:
            List of ConfidenceInterval objects.
        """
        total = len(df)
        if total == 0:
            return []

        option_counts = df["selected_option"].value_counts()
        results = []

        for option, count in option_counts.items():
            p = count / total
            se = np.sqrt(p * (1 - p) / total)
            moe = self.z_score * se

            results.append(
                ConfidenceInterval(
                    option=option,
                    proportion=round(p, 4),
                    ci_lower=round(max(0, p - moe), 4),
                    ci_upper=round(min(1, p + moe), 4),
                    margin_of_error=round(moe, 4),
                    sample_size=total,
                )
            )

        return sorted(results, key=lambda x: x.proportion, reverse=True)

    def compute_margin_of_error(
        self, df: pd.DataFrame
    ) -> list[dict]:
        """Compute margin of error summary per option.

        Args:
            df: DataFrame with 'selected_option' column.

        Returns:
            List of dicts with MoE per option.
        """
        total = len(df)
        if total == 0:
            return []

        option_counts = df["selected_option"].value_counts()
        results = []

        for option, count in option_counts.items():
            p = count / total
            se = np.sqrt(p * (1 - p) / total)
            moe = self.z_score * se

            results.append(
                {
                    "option": option,
                    "count": int(count),
                    "proportion": round(p, 4),
                    "proportion_pct": round(p * 100, 2),
                    "margin_of_error": round(moe, 4),
                    "moe_pct": round(moe * 100, 2),
                    "ci_lower_pct": round(max(0, (p - moe) * 100), 2),
                    "ci_upper_pct": round(min(100, (p + moe) * 100), 2),
                }
            )

        return sorted(results, key=lambda x: x["proportion"], reverse=True)

    def frequency_distribution(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute frequency distribution of options.

        Args:
            df: DataFrame with 'selected_option' column.

        Returns:
            DataFrame with frequency, percentage, and cumulative stats.
        """
        total = len(df)
        if total == 0:
            return pd.DataFrame()

        freq = df["selected_option"].value_counts().reset_index()
        freq.columns = ["option", "count"]
        freq["percentage"] = (freq["count"] / total * 100).round(2)
        freq["cumulative_count"] = freq["count"].cumsum()
        freq["cumulative_pct"] = (freq["cumulative_count"] / total * 100).round(2)

        return freq
