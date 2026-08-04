/**
 * App Module - Main application logic
 * Survey Analytics Platform
 */

const App = (() => {
    let currentPage = 'overview';
    let filters = { age: 'All', gender: 'All', region: 'All' };

    /**
     * Initialize the application
     */
    async function init() {
        setupNavigation();
        setupTabs();
        setupFilters();
        setupMobileMenu();

        try {
            await DataManager.loadMetrics();
            hideLoading();
            renderCurrentPage();
            populateFilters();
        } catch (error) {
            showError();
        }
    }

    /**
     * Set up page navigation
     */
    function setupNavigation() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                navigateTo(page);
            });
        });
    }

    /**
     * Navigate to a specific page
     * @param {string} page - Page identifier
     */
    function navigateTo(page) {
        currentPage = page;

        // Update nav links
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        document.querySelector(`.nav-link[data-page="${page}"]`).classList.add('active');

        // Update pages
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.getElementById(`page-${page}`).classList.add('active');

        renderCurrentPage();
    }

    /**
     * Render the current page content
     */
    function renderCurrentPage() {
        switch (currentPage) {
            case 'overview':
                renderOverview();
                break;
            case 'demographics':
                renderDemographics();
                break;
            case 'statistics':
                renderStatistics();
                break;
        }
    }

    /**
     * Render the Executive Overview page
     */
    function renderOverview() {
        const summary = DataManager.getFilteredExecutiveSummary(filters);
        const validation = DataManager.getValidation();
        const shares = DataManager.getFilteredOptionShares(filters);
        const insights = DataManager.getExecutiveInsights();

        // KPI Cards
        document.getElementById('kpi-total').textContent = DataManager.formatNumber(summary.total_responses);
        document.getElementById('kpi-leading').textContent = summary.leading_option || '--';
        document.getElementById('kpi-leading-pct').textContent = DataManager.formatPercent(summary.leading_percentage) + ' share';
        document.getElementById('kpi-margin').textContent = DataManager.formatPercent(summary.lead_margin);
        document.getElementById('kpi-missing').textContent = DataManager.formatPercent(100 - validation.missing_percentage);

        // Charts
        Charts.renderDistributionBar('chart-distribution', shares);
        Charts.renderShareDonut('chart-pie', shares);

        // Insights
        renderInsights(insights);
    }

    /**
     * Render executive insights
     * @param {Array} insights - List of insights
     */
    function renderInsights(insights) {
        const container = document.getElementById('insights-container');
        if (!insights || insights.length === 0) {
            container.innerHTML = '<p class="no-data">No insights available</p>';
            return;
        }

        container.innerHTML = insights.map(insight => `
            <div class="insight-box ${insight.severity}">
                <div class="insight-category">${insight.category}</div>
                <div class="insight-title">${insight.title}</div>
                <div class="insight-desc">${insight.description}</div>
            </div>
        `).join('');
    }

    /**
     * Render the Demographic & Travel Class Analysis page
     */
    function renderDemographics() {
        const crossTabs = DataManager.getCrossTabulations();
        const regional = DataManager.getRegionalAnalysis();

        // Age heatmap
        if (crossTabs.age_group && crossTabs.age_group.length > 0) {
            Charts.renderHeatmap('chart-age-heatmap', crossTabs.age_group, 'age_group');
            renderCrossTabTable('table-age', crossTabs.age_group, 'age_group');
        }

        // Gender heatmap
        if (crossTabs.gender && crossTabs.gender.length > 0) {
            Charts.renderHeatmap('chart-gender-heatmap', crossTabs.gender, 'gender');
            renderCrossTabTable('table-gender', crossTabs.gender, 'gender');
        }

        // Travel class bar chart
        if (regional.vote_shares && regional.vote_shares.length > 0) {
            Charts.renderRegionalBar('chart-regional-bar', regional.vote_shares);
        }

        // Travel class leads table
        if (regional.leads && regional.leads.length > 0) {
            renderRegionalLeadsTable('table-regional', regional.leads);
        }
    }

    /**
     * Render a cross-tabulation table
     * @param {string} elementId - DOM element ID
     * @param {Array} data - Cross-tab data
     * @param {string} rowKey - Key for row labels
     */
    function renderCrossTabTable(elementId, data, rowKey) {
        const container = document.getElementById(elementId);
        if (!data || data.length === 0) {
            container.innerHTML = '<p class="no-data">No data available</p>';
            return;
        }

        const allKeys = Object.keys(data[0]);
        const optionCols = allKeys.filter(k => k !== rowKey && k !== 'index');

        const headerLabel = rowKey === 'region' ? 'TRAVEL CLASS' : rowKey.replace('_', ' ').toUpperCase();

        let html = '<table class="data-table"><thead><tr>';
        html += `<th>${headerLabel}</th>`;
        optionCols.forEach(col => {
            html += `<th>${col}</th>`;
        });
        html += '</tr></thead><tbody>';

        data.forEach(row => {
            html += '<tr>';
            html += `<td><strong>${row[rowKey] || row.index}</strong></td>`;
            optionCols.forEach(col => {
                const val = row[col] || 0;
                html += `<td>${val.toFixed(1)}%</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    }

    /**
     * Render travel class leads table
     * @param {string} elementId - DOM element ID
     * @param {Array} leads - Travel class leads data
     */
    function renderRegionalLeadsTable(elementId, leads) {
        const container = document.getElementById(elementId);
        if (!leads || leads.length === 0) {
            container.innerHTML = '<p class="no-data">No data available</p>';
            return;
        }

        let html = '<table class="data-table"><thead><tr>';
        html += '<th>Rank</th><th>Travel Class</th><th>Status</th><th>Passengers</th><th>Total</th><th>Satisfaction Rate</th>';
        html += '</tr></thead><tbody>';

        leads.forEach(lead => {
            html += '<tr>';
            html += `<td>${lead.rank}</td>`;
            html += `<td><strong>${lead.region}</strong></td>`;
            html += `<td>${lead.selected_option}</td>`;
            html += `<td>${lead.count.toLocaleString()}</td>`;
            html += `<td>${lead.region_total.toLocaleString()}</td>`;
            html += `<td>${lead.lead_share_pct.toFixed(1)}%</td>`;
            html += '</tr>';
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    }

    /**
     * Render the Statistical Summary page
     */
    function renderStatistics() {
        const chi2 = DataManager.getChiSquareTests();
        const ciData = DataManager.getConfidenceIntervals();
        const moeData = DataManager.getMarginOfError();

        // Chi-Square table
        renderChiSquareTable(chi2);

        // Confidence Interval chart
        Charts.renderConfidenceIntervals('chart-ci', ciData);

        // Margin of Error table
        renderMoETable(moeData);
    }

    /**
     * Render Chi-Square results table
     * @param {Object} chi2 - Chi-square test results
     */
    function renderChiSquareTable(chi2) {
        const container = document.getElementById('table-chi2');
        const interpretationEl = document.getElementById('chi2-interpretation');

        if (!chi2 || Object.keys(chi2).length === 0) {
            container.innerHTML = '<p class="no-data">No chi-square data available</p>';
            return;
        }

        const tests = [
            { label: 'Age Group vs Satisfaction', data: chi2.age_group },
            { label: 'Gender vs Satisfaction', data: chi2.gender },
            { label: 'Travel Class vs Satisfaction', data: chi2.region },
        ];

        let html = '<table class="data-table"><thead><tr>';
        html += '<th>Test</th><th>Chi-Square (χ²)</th><th>p-value</th><th>df</th><th>Cramér\'s V</th><th>Significant</th>';
        html += '</tr></thead><tbody>';

        tests.forEach(test => {
            const d = test.data;
            if (!d) return;
            const sigClass = d.is_significant ? 'significant' : 'not-significant';
            html += '<tr>';
            html += `<td><strong>${test.label}</strong></td>`;
            html += `<td>${d.chi2.toFixed(3)}</td>`;
            html += `<td>${DataManager.formatPValue(d.p_value)}</td>`;
            html += `<td>${d.degrees_of_freedom}</td>`;
            html += `<td>${d.cramers_v.toFixed(3)}</td>`;
            html += `<td class="${sigClass}">${d.is_significant ? 'Yes' : 'No'}</td>`;
            html += '</tr>';
        });

        html += '</tbody></table>';
        container.innerHTML = html;

        // Business-focused interpretation
        const classTest = chi2.region;
        const ageTest = chi2.age_group;
        const genderTest = chi2.gender;

        if (classTest && ageTest && genderTest) {
            const classV = classTest.cramers_v;
            const ageV = ageTest.cramers_v;
            const genderV = genderTest.cramers_v;

            let classEffect = 'negligible';
            if (classV >= 0.5) classEffect = 'strong';
            else if (classV >= 0.2) classEffect = 'moderate';
            else if (classV >= 0.1) classEffect = 'small';

            let ageEffect = 'negligible';
            if (ageV >= 0.5) ageEffect = 'strong';
            else if (ageV >= 0.2) ageEffect = 'moderate';
            else if (ageV >= 0.1) ageEffect = 'small';

            interpretationEl.innerHTML = `
                <strong>Key Statistical Findings:</strong><br><br>
                <strong>Travel Class</strong> has the <strong>strongest</strong> association with passenger satisfaction (Cramér's V = ${classV.toFixed(3)}, p < 0.001). This ${classEffect} effect confirms that cabin class is the primary driver of passenger experience.<br><br>
                <strong>Age Group</strong> demonstrates a <strong>${ageEffect}</strong> association with satisfaction (V = ${ageV.toFixed(3)}). Younger and older passengers show distinct satisfaction patterns compared to middle-aged travelers.<br><br>
                <strong>Gender</strong> differences are statistically significant (V = ${genderV.toFixed(3)}) but have a <strong>negligible practical effect</strong>. Male and female passengers report nearly identical satisfaction levels.<br><br>
                <em>Significance level: α = 0.05</em>
            `;
        }
    }

    /**
     * Render Margin of Error table
     * @param {Array} moeData - Margin of error data
     */
    function renderMoETable(moeData) {
        const container = document.getElementById('table-moe');

        if (!moeData || moeData.length === 0) {
            container.innerHTML = '<p class="no-data">No MoE data available</p>';
            return;
        }

        let html = '<table class="data-table"><thead><tr>';
        html += '<th>Satisfaction Status</th><th>Passengers</th><th>Rate</th><th>MoE</th><th>CI Lower</th><th>CI Upper</th>';
        html += '</tr></thead><tbody>';

        moeData.forEach(row => {
            html += '<tr>';
            html += `<td><strong>${row.option}</strong></td>`;
            html += `<td>${row.count.toLocaleString()}</td>`;
            html += `<td>${row.proportion_pct.toFixed(2)}%</td>`;
            html += `<td>±${row.moe_pct.toFixed(2)}%</td>`;
            html += `<td>${row.ci_lower_pct.toFixed(2)}%</td>`;
            html += `<td>${row.ci_upper_pct.toFixed(2)}%</td>`;
            html += '</tr>';
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    }

    /**
     * Set up tab switching
     */
    function setupTabs() {
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const tabId = tab.dataset.tab;

                // Update tab buttons
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                // Update tab content
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                document.getElementById(`tab-${tabId}`).classList.add('active');
            });
        });
    }

    /**
     * Set up filter controls
     */
    function setupFilters() {
        ['filter-age', 'filter-gender', 'filter-region'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.addEventListener('change', () => {
                    filters.age = document.getElementById('filter-age').value;
                    filters.gender = document.getElementById('filter-gender').value;
                    filters.region = document.getElementById('filter-region').value;
                    renderCurrentPage();
                });
            }
        });

        const clearBtn = document.getElementById('clearFilters');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                document.getElementById('filter-age').value = 'All';
                document.getElementById('filter-gender').value = 'All';
                document.getElementById('filter-region').value = 'All';
                filters.age = 'All';
                filters.gender = 'All';
                filters.region = 'All';
                renderCurrentPage();
            });
        }
    }

    /**
     * Populate filter dropdowns
     */
    function populateFilters() {
        const fields = [
            { id: 'filter-age', field: 'age_group' },
            { id: 'filter-gender', field: 'gender' },
            { id: 'filter-region', field: 'region' },
        ];

        fields.forEach(({ id, field }) => {
            const select = document.getElementById(id);
            if (!select) return;

            const values = DataManager.getUniqueValues(field);
            values.forEach(val => {
                const option = document.createElement('option');
                option.value = val;
                option.textContent = val;
                select.appendChild(option);
            });
        });
    }

    /**
     * Set up mobile menu toggle
     */
    function setupMobileMenu() {
        const toggle = document.getElementById('menuToggle');
        const sidebar = document.getElementById('sidebar');

        if (toggle && sidebar) {
            toggle.addEventListener('click', () => {
                sidebar.classList.toggle('open');
            });

            // Close sidebar when clicking outside
            document.addEventListener('click', (e) => {
                if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
                    sidebar.classList.remove('open');
                }
            });
        }
    }

    /**
     * Hide loading overlay
     */
    function hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) overlay.style.display = 'none';
    }

    /**
     * Show error message
     */
    function showError() {
        const overlay = document.getElementById('loadingOverlay');
        const error = document.getElementById('errorMessage');
        if (overlay) overlay.style.display = 'none';
        if (error) error.style.display = 'block';
    }

    return { init };
})();

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', App.init);
