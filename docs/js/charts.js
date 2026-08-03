/**
 * Charts Module - Plotly chart rendering
 * Airline Passenger Satisfaction Dashboard
 */

const Charts = (() => {
    const COLORS = ['#28A745', '#D4AF37', '#1B2A4A', '#4A6FA5', '#E74C3C', '#9B59B6', '#1ABC9C', '#F39C12'];

    const LAYOUT_DEFAULTS = {
        font: { family: 'Inter, sans-serif', size: 12 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        margin: { t: 20, b: 40, l: 50, r: 20 },
    };

    /**
     * Render the response distribution bar chart
     * @param {string} elementId - DOM element ID
     * @param {Array} optionShares - Option share data
     */
    function renderDistributionBar(elementId, optionShares) {
        if (!optionShares || optionShares.length === 0) return;

        const labels = optionShares.map(d => d.option);
        const values = optionShares.map(d => d.count);
        const percentages = optionShares.map(d => d.share_pct);

        const trace = {
            x: labels,
            y: values,
            type: 'bar',
            marker: {
                color: COLORS.slice(0, labels.length),
                line: { width: 0 },
            },
            text: percentages.map(p => p.toFixed(1) + '%'),
            textposition: 'outside',
            textfont: { size: 11, color: '#2C3E50' },
            hovertemplate: '<b>%{x}</b><br>Count: %{y}<br>Share: %{text}<extra></extra>',
        };

        const layout = {
            ...LAYOUT_DEFAULTS,
            xaxis: { title: 'Option', tickangle: 0 },
            yaxis: { title: 'Count' },
            showlegend: false,
        };

        Plotly.newPlot(elementId, [trace], layout, { responsive: true, displayModeBar: false });
    }

    /**
     * Render the share breakdown donut chart
     * @param {string} elementId - DOM element ID
     * @param {Array} optionShares - Option share data
     */
    function renderShareDonut(elementId, optionShares) {
        if (!optionShares || optionShares.length === 0) return;

        const trace = {
            labels: optionShares.map(d => d.option),
            values: optionShares.map(d => d.count),
            type: 'pie',
            hole: 0.45,
            marker: {
                colors: COLORS.slice(0, optionShares.length),
            },
            textinfo: 'label+percent',
            textposition: 'inside',
            textfont: { size: 11 },
            hovertemplate: '<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>',
            showlegend: false,
        };

        const layout = {
            ...LAYOUT_DEFAULTS,
            margin: { t: 10, b: 10, l: 10, r: 10 },
        };

        Plotly.newPlot(elementId, [trace], layout, { responsive: true, displayModeBar: false });
    }

    /**
     * Render a heatmap for cross-tabulation
     * @param {string} elementId - DOM element ID
     * @param {Array} crossTabData - Cross-tabulation data
     * @param {string} rowKey - Key for row labels
     */
    function renderHeatmap(elementId, crossTabData, rowKey) {
        if (!crossTabData || crossTabData.length === 0) return;

        // Extract option columns (all keys except rowKey and 'index')
        const allKeys = Object.keys(crossTabData[0]);
        const optionCols = allKeys.filter(k => k !== rowKey && k !== 'index');

        const zValues = [];
        const yLabels = [];

        crossTabData.forEach(row => {
            const label = row[rowKey] || row.index;
            yLabels.push(label);
            const rowData = optionCols.map(col => row[col] || 0);
            zValues.push(rowData);
        });

        const trace = {
            z: zValues,
            x: optionCols,
            y: yLabels,
            type: 'heatmap',
            colorscale: [
                [0, '#FFF3E0'],
                [0.5, '#FF9800'],
                [1, '#E65100'],
            ],
            text: zValues.map(row => row.map(v => v.toFixed(1) + '%')),
            texttemplate: '%{text}',
            textfont: { size: 11 },
            hovertemplate: '<b>%{y}</b> vs <b>%{x}</b><br>Share: %{text}<extra></extra>',
            showscale: true,
            colorbar: {
                title: '% Share',
                titleside: 'right',
                thickness: 12,
            },
        };

        const layout = {
            ...LAYOUT_DEFAULTS,
            xaxis: { title: 'Option' },
            yaxis: { title: '', autorange: 'reversed' },
            margin: { t: 10, b: 80, l: 80, r: 80 },
        };

        Plotly.newPlot(elementId, [trace], layout, { responsive: true, displayModeBar: false });
    }

    /**
     * Render travel class vote shares stacked bar chart
     * @param {string} elementId - DOM element ID
     * @param {Array} regionalVoteShares - Travel class vote share data
     */
    function renderRegionalBar(elementId, regionalVoteShares) {
        if (!regionalVoteShares || regionalVoteShares.length === 0) return;

        // Group by travel class
        const regions = [...new Set(regionalVoteShares.map(d => d.region))];
        const options = [...new Set(regionalVoteShares.map(d => d.selected_option))];

        const traces = options.map((option, idx) => ({
            name: option,
            x: regions,
            y: regions.map(region => {
                const match = regionalVoteShares.find(
                    d => d.region === region && d.selected_option === option
                );
                return match ? match.share_pct : 0;
            }),
            type: 'bar',
            marker: { color: COLORS[idx % COLORS.length] },
            hovertemplate: '<b>%{x}</b><br>' + option + ': %{y:.1f}%<extra></extra>',
        }));

        const layout = {
            ...LAYOUT_DEFAULTS,
            barmode: 'stack',
            xaxis: { title: 'Travel Class' },
            yaxis: { title: 'Share (%)' },
            legend: { orientation: 'h', y: -0.2, x: 0.5, xanchor: 'center' },
        };

        Plotly.newPlot(elementId, traces, layout, { responsive: true, displayModeBar: false });
    }

    /**
     * Render 95% confidence interval error bar chart
     * @param {string} elementId - DOM element ID
     * @param {Array} ciData - Confidence interval data
     */
    function renderConfidenceIntervals(elementId, ciData) {
        if (!ciData || ciData.length === 0) return;

        const yLabels = ciData.map(d => d.option);
        const xValues = ciData.map(d => d.proportion);
        const errorMinus = ciData.map(d => d.proportion - d.ci_lower);
        const errorPlus = ciData.map(d => d.ci_upper - d.proportion);

        const trace = {
            x: xValues,
            y: yLabels,
            error_x: {
                type: 'data',
                symmetric: false,
                array: errorPlus,
                arrayminus: errorMinus,
                color: COLORS.slice(0, ciData.length),
                thickness: 2,
                width: 8,
            },
            mode: 'markers',
            type: 'scatter',
            marker: {
                size: 12,
                color: COLORS.slice(0, ciData.length),
            },
            hovertemplate: '<b>%{y}</b><br>Proportion: %{x:.1%}<extra></extra>',
        };

        const layout = {
            ...LAYOUT_DEFAULTS,
            xaxis: {
                title: 'Proportion',
                tickformat: '.0%',
                range: [0, 1],
            },
            yaxis: { title: '' },
            showlegend: false,
        };

        Plotly.newPlot(elementId, [trace], layout, { responsive: true, displayModeBar: false });
    }

    return {
        renderDistributionBar,
        renderShareDonut,
        renderHeatmap,
        renderRegionalBar,
        renderConfidenceIntervals,
        COLORS,
    };
})();
