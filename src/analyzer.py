"""Survey Analyzer Module - Cross-tabulations and aggregations."""

from typing import Optional

import pandas as pd


class SurveyAnalyzer:
    """Performs demographic and regional cross-tabulations."""

    def __init__(self) -> None:
        """Initialize analyzer."""
        pass

    def compute_option_shares(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute overall option share percentages.

        Args:
            df: Survey DataFrame.

        Returns:
            DataFrame with option, count, and share_pct.
        """
        total = len(df)
        if total == 0:
            return pd.DataFrame()

        shares = df["selected_option"].value_counts().reset_index()
        shares.columns = ["option", "count"]
        shares["share_pct"] = (shares["count"] / total * 100).round(2)

        return shares

    def compute_age_cross_tab(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cross-tabulate age groups against selected options.

        Args:
            df: Survey DataFrame.

        Returns:
            Pivot table of age groups vs options with row percentages.
        """
        if df.empty:
            return pd.DataFrame()

        ct = pd.crosstab(df["age_group"], df["selected_option"], margins=False)
        ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100

        return ct_pct.round(2)

    def compute_gender_cross_tab(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cross-tabulate gender against selected options.

        Args:
            df: Survey DataFrame.

        Returns:
            Pivot table of gender vs options with row percentages.
        """
        if df.empty:
            return pd.DataFrame()

        ct = pd.crosstab(df["gender"], df["selected_option"], margins=False)
        ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100

        return ct_pct.round(2)

    def compute_region_cross_tab(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cross-tabulate regions against selected options.

        Args:
            df: Survey DataFrame.

        Returns:
            Pivot table of regions vs options with row percentages.
        """
        if df.empty:
            return pd.DataFrame()

        ct = pd.crosstab(df["region"], df["selected_option"], margins=False)
        ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100

        return ct_pct.round(2)

    def compute_regional_vote_shares(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute vote shares per region.

        Args:
            df: Survey DataFrame.

        Returns:
            DataFrame with region, option, count, and share.
        """
        if df.empty:
            return pd.DataFrame()

        regional = (
            df.groupby(["region", "selected_option"])
            .size()
            .reset_index(name="count")
        )

        region_totals = df.groupby("region").size().reset_index(name="region_total")
        regional = regional.merge(region_totals, on="region")
        regional["share_pct"] = (regional["count"] / regional["region_total"] * 100).round(2)

        return regional

    def compute_regional_leads(self, df: pd.DataFrame) -> pd.DataFrame:
        """Determine leading option per region with rankings.

        Args:
            df: Survey DataFrame.

        Returns:
            DataFrame with region, leading_option, lead_count, lead_share.
        """
        if df.empty:
            return pd.DataFrame()

        regional_votes = (
            df.groupby(["region", "selected_option"])
            .size()
            .reset_index(name="count")
        )

        idx = regional_votes.groupby("region")["count"].idxmax()
        leads = regional_votes.loc[idx].copy()

        region_totals = df.groupby("region").size().reset_index(name="region_total")
        leads = leads.merge(region_totals, on="region")
        leads["lead_share_pct"] = (leads["count"] / leads["region_total"] * 100).round(2)
        leads = leads.sort_values("lead_share_pct", ascending=False)
        leads["rank"] = range(1, len(leads) + 1)

        return leads[["rank", "region", "selected_option", "count", "region_total", "lead_share_pct"]]

    def filter_by_demographics(
        self,
        df: pd.DataFrame,
        age_group: Optional[str] = None,
        gender: Optional[str] = None,
        region: Optional[str] = None,
    ) -> pd.DataFrame:
        """Filter DataFrame by demographic criteria.

        Args:
            df: Input DataFrame.
            age_group: Optional age group filter.
            gender: Optional gender filter.
            region: Optional region filter.

        Returns:
            Filtered DataFrame.
        """
        result = df.copy()

        if age_group and age_group != "All":
            result = result[result["age_group"] == age_group]

        if gender and gender != "All":
            result = result[result["gender"] == gender]

        if region and region != "All":
            result = result[result["region"] == region]

        return result
