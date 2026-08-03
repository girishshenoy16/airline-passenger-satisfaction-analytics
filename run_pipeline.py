#!/usr/bin/env python3
"""Pipeline Runner - Execute analytics pipeline and export data for GitHub Pages dashboard."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types."""

    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

from src.data_ingestion import SurveyDataIngestor
from src.data_validator import SurveyDataValidator
from src.feature_engineering import FeatureEngineer
from src.statistical_engine import StatisticalEngine
from src.analyzer import SurveyAnalyzer
from src.insights_engine import InsightsEngine


def load_config(config_path: str = "config/settings.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def run_pipeline() -> dict:
    """Execute the full analytics pipeline.

    Returns:
        Dictionary with all analysis results.
    """
    config = load_config()
    config_path = "config/settings.yaml"

    # Initialize modules
    ingestor = SurveyDataIngestor(config_path)
    validator = SurveyDataValidator(config_path)
    feature_eng = FeatureEngineer()
    stat_engine = StatisticalEngine(config_path)
    analyzer = SurveyAnalyzer()
    insights_engine = InsightsEngine(config_path)

    # Data Ingestion
    print("Loading Airline Passenger Satisfaction dataset...")
    df = ingestor.load_airline_dataset("data/raw")
    print(f"Loaded {len(df)} records from Airline dataset")

    # Validation
    print("Running data validation...")
    validation = validator.validate(df)
    clean_df, duplicates_removed = validator.get_clean_data(df)
    print(f"  Valid: {validation.is_valid}")
    print(f"  Total records: {validation.total_records}")
    print(f"  Missing rate: {validation.missing_percentage:.2f}%")
    print(f"  Duplicates removed: {duplicates_removed}")

    # Feature Engineering
    print("Computing features...")
    featured_df = feature_eng.compute_features(clean_df)
    print(f"  Features added: response_share_pct, participation_count, regional_rank, demographic_segment")

    # Statistical Analysis
    print("Running statistical analysis...")
    option_shares = analyzer.compute_option_shares(featured_df)
    freq_dist = stat_engine.frequency_distribution(featured_df)
    ci_results = stat_engine.compute_confidence_intervals(featured_df)
    moe_results = stat_engine.compute_margin_of_error(featured_df)

    # Cross-tabulations
    age_cross = analyzer.compute_age_cross_tab(featured_df)
    gender_cross = analyzer.compute_gender_cross_tab(featured_df)
    region_cross = analyzer.compute_region_cross_tab(featured_df)
    regional_votes = analyzer.compute_regional_vote_shares(featured_df)
    regional_leads = analyzer.compute_regional_leads(featured_df)

    # Group sizes for filtering
    age_sizes = featured_df["age_group"].value_counts().to_dict()
    gender_sizes = featured_df["gender"].value_counts().to_dict()
    region_sizes = featured_df["region"].value_counts().to_dict()

    # Chi-Square Tests
    chi2_age = stat_engine.chi_square_test(featured_df, "age_group", "selected_option")
    chi2_gender = stat_engine.chi_square_test(featured_df, "gender", "selected_option")
    chi2_region = stat_engine.chi_square_test(featured_df, "region", "selected_option")

    print(f"  Chi-Square (Age): chi2={chi2_age.chi2}, p={chi2_age.p_value}, V={chi2_age.cramers_v}")
    print(f"  Chi-Square (Gender): chi2={chi2_gender.chi2}, p={chi2_gender.p_value}, V={chi2_gender.cramers_v}")
    print(f"  Chi-Square (Region): chi2={chi2_region.chi2}, p={chi2_region.p_value}, V={chi2_region.cramers_v}")

    # Executive Insights
    print("Generating executive insights...")
    executive_insights = insights_engine.generate_insights(
        featured_df, option_shares, validation, chi2_age, chi2_gender, chi2_region
    )
    exec_summary = insights_engine.get_executive_summary(option_shares, len(featured_df))

    for insight in executive_insights:
        print(f"  [{insight.severity.upper()}] {insight.category}: {insight.title}")

    return {
        "raw_df": df,
        "clean_df": featured_df,
        "validation": validation,
        "duplicates_removed": duplicates_removed,
        "option_shares": option_shares,
        "freq_dist": freq_dist,
        "ci_results": ci_results,
        "moe_results": moe_results,
        "age_cross": age_cross,
        "gender_cross": gender_cross,
        "region_cross": region_cross,
        "regional_votes": regional_votes,
        "regional_leads": regional_leads,
        "chi2_age": chi2_age,
        "chi2_gender": chi2_gender,
        "chi2_region": chi2_region,
        "executive_insights": executive_insights,
        "exec_summary": exec_summary,
        "age_sizes": age_sizes,
        "gender_sizes": gender_sizes,
        "region_sizes": region_sizes,
    }


def export_results(results: dict, output_dir: str = ".") -> None:
    """Export analysis results to CSV and JSON files.

    Args:
        results: Dictionary with all analysis results.
        output_dir: Root directory for output files.
    """
    output_path = Path(output_dir)

    # Export processed CSV
    csv_dir = output_path / "data" / "processed"
    csv_dir.mkdir(parents=True, exist_ok=True)
    csv_file = csv_dir / "processed_survey_data.csv"
    results["clean_df"].to_csv(csv_file, index=False)
    print(f"\nExported CSV: {csv_file}")

    # Export dashboard metrics JSON
    json_dir = output_path / "outputs"
    json_dir.mkdir(parents=True, exist_ok=True)
    json_file = json_dir / "dashboard_metrics.json"

    metrics = {
        "executive_summary": results["exec_summary"],
        "validation": {
            "total_records": results["validation"].total_records,
            "missing_percentage": round(results["validation"].missing_percentage, 2),
            "duplicate_count": results["validation"].duplicate_count,
            "duplicate_percentage": round(results["validation"].duplicate_percentage, 2),
            "is_valid": results["validation"].is_valid,
        },
        "option_shares": results["option_shares"].to_dict(orient="records")
        if not results["option_shares"].empty else [],
        "frequency_distribution": results["freq_dist"].to_dict(orient="records")
        if not results["freq_dist"].empty else [],
        "chi_square_tests": {
            "age_group": {
                "chi2": results["chi2_age"].chi2,
                "p_value": results["chi2_age"].p_value,
                "degrees_of_freedom": results["chi2_age"].degrees_of_freedom,
                "cramers_v": results["chi2_age"].cramers_v,
                "is_significant": results["chi2_age"].is_significant,
            },
            "gender": {
                "chi2": results["chi2_gender"].chi2,
                "p_value": results["chi2_gender"].p_value,
                "degrees_of_freedom": results["chi2_gender"].degrees_of_freedom,
                "cramers_v": results["chi2_gender"].cramers_v,
                "is_significant": results["chi2_gender"].is_significant,
            },
            "region": {
                "chi2": results["chi2_region"].chi2,
                "p_value": results["chi2_region"].p_value,
                "degrees_of_freedom": results["chi2_region"].degrees_of_freedom,
                "cramers_v": results["chi2_region"].cramers_v,
                "is_significant": results["chi2_region"].is_significant,
            },
        },
        "confidence_intervals": [
            {
                "option": ci.option,
                "proportion": ci.proportion,
                "ci_lower": ci.ci_lower,
                "ci_upper": ci.ci_upper,
                "margin_of_error": ci.margin_of_error,
                "sample_size": ci.sample_size,
            }
            for ci in results["ci_results"]
        ],
        "margin_of_error": results["moe_results"],
        "cross_tabulations": {
            "age_group": results["age_cross"].reset_index().to_dict(orient="records")
            if not results["age_cross"].empty else [],
            "gender": results["gender_cross"].reset_index().to_dict(orient="records")
            if not results["gender_cross"].empty else [],
            "region": results["region_cross"].reset_index().to_dict(orient="records")
            if not results["region_cross"].empty else [],
        },
        "regional_analysis": {
            "vote_shares": results["regional_votes"].to_dict(orient="records")
            if not results["regional_votes"].empty else [],
            "leads": results["regional_leads"].to_dict(orient="records")
            if not results["regional_leads"].empty else [],
        },
        "executive_insights": [
            {
                "category": i.category,
                "title": i.title,
                "description": i.description,
                "severity": i.severity,
            }
            for i in results["executive_insights"]
        ],
        "group_sizes": {
            "age_group": results["age_sizes"],
            "gender": results["gender_sizes"],
            "region": results["region_sizes"],
        },
    }

    with open(json_file, "w") as f:
        json.dump(metrics, f, indent=2, cls=NumpyEncoder)
    print(f"Exported JSON: {json_file}")


def main():
    """Main entry point for the pipeline."""
    print("=" * 60)
    print("Airline Passenger Satisfaction Analytics Pipeline")
    print("=" * 60)

    results = run_pipeline()

    export_results(results)

    print("\n" + "=" * 60)
    print("Pipeline completed successfully!")
    print("=" * 60)
    print("\nOutput files:")
    print(f"  - data/processed_survey_data.csv")
    print(f"  - outputs/dashboard_metrics.json")
    print("\nTo view the dashboard, open docs/index.html in a browser")


if __name__ == "__main__":
    main()
