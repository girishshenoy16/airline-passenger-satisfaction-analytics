"""Feature Engineering Module - Response shares, ranks, and demographic segments."""

import pandas as pd


class FeatureEngineer:
    """Computes derived analytical features from raw survey data."""

    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all derived features to the survey DataFrame.

        Args:
            df: Validated survey DataFrame.

        Returns:
            DataFrame with added feature columns.
        """
        result = df.copy()

        result = self._compute_response_share(result)
        result = self._compute_participation_count(result)
        result = self._compute_regional_rank(result)
        result = self._compute_demographic_segment(result)

        return result

    def _compute_response_share(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute percentage share for each option.

        Adds column: response_share_pct
        """
        total = len(df)
        if total == 0:
            df["response_share_pct"] = 0.0
            return df

        option_counts = df["selected_option"].value_counts()
        share_map = (option_counts / total * 100).to_dict()
        df["response_share_pct"] = df["selected_option"].map(share_map).round(2)

        return df

    def _compute_participation_count(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute total participation count per option.

        Adds column: participation_count
        """
        counts = df["selected_option"].value_counts().to_dict()
        df["participation_count"] = df["selected_option"].map(counts)

        return df

    def _compute_regional_rank(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rank regions by their preference for the leading option.

        Adds column: regional_rank
        """
        if df.empty:
            df["regional_rank"] = 0
            return df

        leading_option = df["selected_option"].mode().iloc[0]

        regional_leading = (
            df[df["selected_option"] == leading_option]
            .groupby("region")
            .size()
            .reset_index(name="leading_count")
        )

        regional_total = df.groupby("region").size().reset_index(name="total_count")

        regional_stats = regional_leading.merge(regional_total, on="region")
        regional_stats["share"] = (
            regional_stats["leading_count"] / regional_stats["total_count"]
        )
        regional_stats = regional_stats.sort_values("share", ascending=False)
        regional_stats["regional_rank"] = range(1, len(regional_stats) + 1)

        rank_map = dict(
            zip(regional_stats["region"], regional_stats["regional_rank"])
        )
        df["regional_rank"] = df["region"].map(rank_map).fillna(0).astype(int)

        return df

    def _compute_demographic_segment(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create demographic segment labels.

        Adds column: demographic_segment
        """
        df["demographic_segment"] = (
            df["age_group"].astype(str)
            + " | "
            + df["gender"].astype(str)
        )

        return df
