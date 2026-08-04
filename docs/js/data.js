/**
 * Data Module - Load and process dashboard data
 * Airline Passenger Satisfaction Dashboard
 */

const DataManager = (() => {
    let metricsData = null;

    /**
     * Load the dashboard metrics JSON file
     * @returns {Promise<Object>} The metrics data
     */
    async function loadMetrics() {
        try {
            const response = await fetch('outputs/dashboard_metrics.json');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            metricsData = await response.json();
            return metricsData;
        } catch (error) {
            console.error('Failed to load metrics:', error);
            throw error;
        }
    }

    /**
     * Get the full metrics data object
     * @returns {Object|null} Metrics data
     */
    function getData() {
        return metricsData;
    }

    /**
     * Get executive summary
     * @returns {Object} Executive summary metrics
     */
    function getExecutiveSummary() {
        return metricsData?.executive_summary || {};
    }

    /**
     * Get validation results
     * @returns {Object} Validation metrics
     */
    function getValidation() {
        return metricsData?.validation || {};
    }

    /**
     * Get option shares
     * @returns {Array} Option share data
     */
    function getOptionShares() {
        return metricsData?.option_shares || [];
    }

    /**
     * Get frequency distribution
     * @returns {Array} Frequency distribution data
     */
    function getFrequencyDistribution() {
        return metricsData?.frequency_distribution || [];
    }

    /**
     * Get chi-square test results
     * @returns {Object} Chi-square results for age, gender, region
     */
    function getChiSquareTests() {
        return metricsData?.chi_square_tests || {};
    }

    /**
     * Get confidence intervals
     * @returns {Array} Confidence interval data
     */
    function getConfidenceIntervals() {
        return metricsData?.confidence_intervals || [];
    }

    /**
     * Get margin of error data
     * @returns {Array} MoE data per option
     */
    function getMarginOfError() {
        return metricsData?.margin_of_error || [];
    }

    /**
     * Get cross-tabulations
     * @returns {Object} Cross-tab data for age, gender, region
     */
    function getCrossTabulations() {
        return metricsData?.cross_tabulations || {};
    }

    /**
     * Get regional analysis
     * @returns {Object} Travel class vote shares and leads
     */
    function getRegionalAnalysis() {
        return metricsData?.regional_analysis || {};
    }

    /**
     * Get executive insights
     * @returns {Array} List of executive insights
     */
    function getExecutiveInsights() {
        return metricsData?.executive_insights || [];
    }

    /**
     * Get group sizes for each demographic dimension
     * @returns {Object} Group sizes for age_group, gender, region
     */
    function getGroupSizes() {
        return metricsData?.group_sizes || {};
    }

    /**
     * Get unique values for a specific demographic field
     * @param {string} field - The field name (age_group, gender, region)
     * @returns {Array} Unique values
     */
    function getUniqueValues(field) {
        const groupSizes = getGroupSizes();
        if (groupSizes[field]) {
            return Object.keys(groupSizes[field]);
        }
        return [];
    }

    /**
     * Get filtered option shares based on demographic filters
     * @param {Object} filters - { age: 'All'|string, gender: 'All'|string, region: 'All'|string }
     * @returns {Array} Filtered option shares
     */
    function getFilteredOptionShares(filters) {
        const crossTabs = getCrossTabulations();
        const groupSizes = getGroupSizes();

        // If no filter is active, return overall shares
        if (filters.age === 'All' && filters.gender === 'All' && filters.region === 'All') {
            return getOptionShares();
        }

        // Determine which demographic to filter by (first active filter)
        let filterField = null;
        let filterValue = null;
        let crossTabData = null;

        if (filters.region !== 'All') {
            filterField = 'region';
            filterValue = filters.region;
            crossTabData = crossTabs.region;
        } else if (filters.gender !== 'All') {
            filterField = 'gender';
            filterValue = filters.gender;
            crossTabData = crossTabs.gender;
        } else if (filters.age !== 'All') {
            filterField = 'age_group';
            filterValue = filters.age;
            crossTabData = crossTabs.age_group;
        }

        if (!filterField || !crossTabData) {
            return getOptionShares();
        }

        const row = crossTabData.find(r => (r[filterField] || r.index) === filterValue);
        if (!row) {
            return getOptionShares();
        }

        const groupSize = groupSizes[filterField]?.[filterValue] || 0;
        if (groupSize === 0) {
            return getOptionShares();
        }

        // Build filtered option shares from cross-tab percentages
        const result = [];
        for (const key of Object.keys(row)) {
            if (key === filterField || key === 'index') continue;
            const pct = row[key];
            result.push({
                option: key,
                count: Math.round(groupSize * pct / 100),
                share_pct: pct,
            });
        }

        return result;
    }

    /**
     * Get filtered executive summary
     * @param {Object} filters - Filter object
     * @returns {Object} Filtered executive summary
     */
    function getFilteredExecutiveSummary(filters) {
        if (filters.age === 'All' && filters.gender === 'All' && filters.region === 'All') {
            return getExecutiveSummary();
        }

        const shares = getFilteredOptionShares(filters);
        if (shares.length === 0) {
            return getExecutiveSummary();
        }

        const total = shares.reduce((sum, s) => sum + s.count, 0);
        const sorted = [...shares].sort((a, b) => b.share_pct - a.share_pct);
        const leading = sorted[0];
        const runnerUp = sorted[1];

        return {
            total_responses: total,
            leading_option: leading.option,
            leading_percentage: leading.share_pct,
            lead_margin: runnerUp ? (leading.share_pct - runnerUp.share_pct) : leading.share_pct,
            num_options: shares.length,
            options_analyzed: shares.map(s => s.option),
        };
    }

    /**
     * Format number with comma separators
     * @param {number} num - Number to format
     * @returns {string} Formatted number
     */
    function formatNumber(num) {
        if (num === undefined || num === null) return '--';
        return num.toLocaleString('en-US');
    }

    /**
     * Format percentage
     * @param {number} value - Value to format as percentage
     * @param {number} decimals - Decimal places
     * @returns {string} Formatted percentage
     */
    function formatPercent(value, decimals = 1) {
        if (value === undefined || value === null) return '--';
        return value.toFixed(decimals) + '%';
    }

    /**
     * Format p-value for display
     * @param {number} p - P-value
     * @returns {string} Formatted p-value
     */
    function formatPValue(p) {
        if (p === undefined || p === null) return '--';
        if (p < 0.001) return '< 0.001';
        return p.toFixed(3);
    }

    return {
        loadMetrics,
        getData,
        getExecutiveSummary,
        getFilteredExecutiveSummary,
        getValidation,
        getOptionShares,
        getFilteredOptionShares,
        getFrequencyDistribution,
        getChiSquareTests,
        getConfidenceIntervals,
        getMarginOfError,
        getCrossTabulations,
        getRegionalAnalysis,
        getExecutiveInsights,
        getGroupSizes,
        getUniqueValues,
        formatNumber,
        formatPercent,
        formatPValue,
    };
})();
