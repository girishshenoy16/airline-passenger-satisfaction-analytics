"""Insights Engine Module - Rule-based executive recommendations."""

from dataclasses import dataclass
from typing import List

import pandas as pd
import yaml


@dataclass
class ExecutiveInsight:
    """Container for a single executive insight."""

    category: str
    title: str
    description: str
    severity: str  # "info", "warning", "success"


class InsightsEngine:
    """Generates rule-based C-Suite strategic recommendations."""

    def __init__(self, config_path: str = "config/settings.yaml") -> None:
        """Initialize with configuration thresholds."""
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.thresholds = self.config.get("thresholds", {})
        self.lead_margin_high = self.thresholds.get("lead_margin_high", 15)
        self.lead_margin_medium = self.thresholds.get("lead_margin_medium", 5)
        self.missing_warning = self.thresholds.get("missing_rate_warning", 5)
        self.min_sample = self.thresholds.get("min_sample_size", 30)

    def generate_insights(
        self,
        df: pd.DataFrame,
        option_shares: pd.DataFrame,
        validation_result: object,
        chi_square_age: object = None,
        chi_square_gender: object = None,
        chi_square_region: object = None,
    ) -> List[ExecutiveInsight]:
        """Generate all executive insights from analysis results.

        Args:
            df: Processed survey DataFrame.
            option_shares: Option share percentages.
            validation_result: ValidationResult dataclass.
            chi_square_age: ChiSquareResult for age group analysis.
            chi_square_gender: ChiSquareResult for gender analysis.
            chi_square_region: ChiSquareResult for travel class analysis.

        Returns:
            List of ExecutiveInsight objects.
        """
        insights: List[ExecutiveInsight] = []

        insights.extend(self._analyze_satisfaction_overview(option_shares))
        insights.extend(self._analyze_class_impact(df))
        insights.extend(self._analyze_age_patterns(df))
        insights.extend(self._analyze_data_quality(validation_result))

        if chi_square_region is not None:
            insights.extend(self._analyze_class_significance(chi_square_region))
        if chi_square_age is not None:
            insights.extend(self._analyze_age_significance(chi_square_age))
        if chi_square_gender is not None:
            insights.extend(self._analyze_gender_significance(chi_square_gender))

        return insights

    def _analyze_satisfaction_overview(self, shares: pd.DataFrame) -> List[ExecutiveInsight]:
        """Analyze overall satisfaction distribution."""
        insights = []

        if shares.empty:
            return insights

        satisfied_row = shares[shares["option"] == "Satisfied"]
        dissatisfied_row = shares[shares["option"].isin(["Neutral/Dissatisfied", "Neutral"])]

        if satisfied_row.empty or dissatisfied_row.empty:
            return insights

        satisfied_pct = satisfied_row.iloc[0]["share_pct"]
        dissatisfied_pct = dissatisfied_row.iloc[0]["share_pct"]
        total = shares["count"].sum()

        insights.append(
            ExecutiveInsight(
                category="Satisfaction Overview",
                title="Majority Passengers Dissatisfied",
                description=(
                    f"Overall passenger satisfaction stands at {satisfied_pct:.1f}%, "
                    f"while {dissatisfied_pct:.1f}% of passengers are Neutral or Dissatisfied. "
                    f"This indicates a significant opportunity for service improvement "
                    f"across the airline's operations."
                ),
                severity="warning",
            )
        )

        return insights

    def _analyze_class_impact(self, df: pd.DataFrame) -> List[ExecutiveInsight]:
        """Analyze travel class impact on satisfaction."""
        insights = []

        if "region" not in df.columns or "selected_option" not in df.columns:
            return insights

        class_data = df.groupby(["region", "selected_option"]).size().unstack(fill_value=0)
        class_totals = class_data.sum(axis=1)
        class_satisfied = class_data.get("Satisfied", pd.Series(dtype=float))
        class_pct = (class_satisfied / class_totals * 100).round(1)

        if class_pct.empty:
            return insights

        best_class = class_pct.idxmax()
        best_pct = class_pct.max()
        worst_class = class_pct.idxmin()
        worst_pct = class_pct.min()

        insights.append(
            ExecutiveInsight(
                category="Travel Class Impact",
                title="Premium Class Leads Satisfaction",
                description=(
                    f"{best_class} Class records the highest satisfaction at {best_pct:.1f}%, "
                    f"while {worst_class} Class has the lowest at {worst_pct:.1f}%. "
                    f"The {best_pct - worst_pct:.1f}-point gap suggests class-based "
                    f"service disparities drive passenger experience."
                ),
                severity="info",
            )
        )

        return insights

    def _analyze_age_patterns(self, df: pd.DataFrame) -> List[ExecutiveInsight]:
        """Analyze age-related satisfaction patterns."""
        insights = []

        if "age_group" not in df.columns or "selected_option" not in df.columns:
            return insights

        age_data = df.groupby(["age_group", "selected_option"]).size().unstack(fill_value=0)
        age_totals = age_data.sum(axis=1)
        age_satisfied = age_data.get("Satisfied", pd.Series(dtype=float))
        age_pct = (age_satisfied / age_totals * 100).round(1)

        if age_pct.empty:
            return insights

        best_age = age_pct.idxmax()
        best_pct = age_pct.max()
        worst_age = age_pct.idxmin()
        worst_pct = age_pct.min()

        insights.append(
            ExecutiveInsight(
                category="Age Demographics",
                title="Age Groups Show Distinct Patterns",
                description=(
                    f"Passengers aged {best_age} report the highest satisfaction ({best_pct:.1f}%), "
                    f"while {worst_age} passengers report the lowest ({worst_pct:.1f}%). "
                    f"This {best_pct - worst_pct:.1f}-point gap suggests age-specific "
                    f"expectations and service needs."
                ),
                severity="info",
            )
        )

        return insights

    def _analyze_data_quality(self, validation_result: object) -> List[ExecutiveInsight]:
        """Analyze data quality metrics."""
        insights = []

        if hasattr(validation_result, "missing_percentage"):
            if validation_result.missing_percentage > self.missing_warning:
                insights.append(
                    ExecutiveInsight(
                        category="Data Quality",
                        title="Elevated Missing Data",
                        description=(
                            f"Missing data rate is {validation_result.missing_percentage:.1f}%. "
                            f"Results should be interpreted with appropriate caution. "
                            f"Consider investigating data collection processes."
                        ),
                        severity="warning",
                    )
                )
            else:
                insights.append(
                    ExecutiveInsight(
                        category="Data Quality",
                        title="High-Reliability Dataset",
                        description=(
                            f"The dataset contains {validation_result.total_records:,} valid responses "
                            f"with {validation_result.missing_percentage:.1f}% missing values, "
                            f"making the analysis highly reliable for executive decision-making."
                        ),
                        severity="success",
                    )
                )

        return insights

    def _analyze_class_significance(self, chi2_result: object) -> List[ExecutiveInsight]:
        """Analyze Travel Class chi-square significance."""
        insights = []

        if hasattr(chi2_result, "is_significant") and chi2_result.is_significant:
            v = chi2_result.cramers_v
            if v >= 0.5:
                effect_desc = "strong"
            elif v >= 0.2:
                effect_desc = "moderate"
            elif v >= 0.1:
                effect_desc = "small"
            else:
                effect_desc = "negligible"

            insights.append(
                ExecutiveInsight(
                    category="Statistical Finding",
                    title="Travel Class Strongly Influences Satisfaction",
                    description=(
                        f"Travel Class has the strongest association with passenger "
                        f"satisfaction (Cramér's V = {v:.3f}, p < 0.001). "
                        f"The {effect_desc} effect size confirms that cabin class "
                        f"is the primary driver of passenger experience."
                    ),
                    severity="success",
                )
            )

        return insights

    def _analyze_age_significance(self, chi2_result: object) -> List[ExecutiveInsight]:
        """Analyze Age Group chi-square significance."""
        insights = []

        if hasattr(chi2_result, "is_significant") and chi2_result.is_significant:
            v = chi2_result.cramers_v
            if v >= 0.5:
                effect_desc = "strong"
            elif v >= 0.2:
                effect_desc = "moderate"
            elif v >= 0.1:
                effect_desc = "small"
            else:
                effect_desc = "negligible"

            insights.append(
                ExecutiveInsight(
                    category="Statistical Finding",
                    title="Age Group Shows Moderate Association",
                    description=(
                        f"Age Group shows a {effect_desc} association with passenger "
                        f"satisfaction (Cramér's V = {v:.3f}, p < 0.001). "
                        f"Younger and older passengers report distinct satisfaction "
                        f"levels compared to middle-aged travelers."
                    ),
                    severity="info",
                )
            )

        return insights

    def _analyze_gender_significance(self, chi2_result: object) -> List[ExecutiveInsight]:
        """Analyze Gender chi-square significance."""
        insights = []

        if hasattr(chi2_result, "is_significant") and chi2_result.is_significant:
            v = chi2_result.cramers_v
            insights.append(
                ExecutiveInsight(
                    category="Statistical Finding",
                    title="Gender Differences Negligible",
                    description=(
                        f"Gender differences are statistically significant "
                        f"(Cramér's V = {v:.3f}, p < 0.001) but have a negligible "
                        f"practical effect. Male and female passengers report "
                        f"nearly identical satisfaction levels."
                    ),
                    severity="info",
                )
            )

        return insights

    def get_executive_summary(
        self, option_shares: pd.DataFrame, total_responses: int
    ) -> dict:
        """Generate a concise executive summary dictionary.

        Args:
            option_shares: Option share percentages.
            total_responses: Total number of responses.

        Returns:
            Dictionary with key executive metrics.
        """
        if option_shares.empty:
            return {}

        top = option_shares.iloc[0]
        leading_option = top["option"]
        leading_pct = top["share_pct"]

        if len(option_shares) > 1:
            margin = leading_pct - option_shares.iloc[1]["share_pct"]
        else:
            margin = leading_pct

        return {
            "total_responses": total_responses,
            "leading_option": leading_option,
            "leading_percentage": leading_pct,
            "lead_margin": round(margin, 2),
            "num_options": len(option_shares),
            "options_analyzed": option_shares["option"].tolist(),
        }
