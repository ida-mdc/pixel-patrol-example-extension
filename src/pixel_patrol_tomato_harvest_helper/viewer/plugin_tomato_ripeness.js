
/**
 * Tomato Ripeness by Season plugin - part of the Tomato Harvest Helper Extension.
 *
 * Plots the proportions of unripe, midripe, and ripe tomato pixels computed
 * by TomatoRipenessProcessor (from the actual pixel data) for each season,
 * split by growing environment (greenhouse or outdoors).
 * A stacked bar chart compares ripeness distributions across seasons
 * and growing environments.
 * 
 * Load via the extension manifest (recommended):
 *   ?extension=https://your-host/extension.json
 *
 * Or standalone:
 *   ?plugin=https://your-host/plugin_dives_logged.js
 */

const SEASON_ORDER = ['spring', 'summer', 'autumn', 'winter'];

const RIPENESS = [
{ key: 'unripe', label: 'Unripe', color: '#5a9e49' },
{ key: 'midripe', label: 'Midripe', color: '#e7ad38' },
{ key: 'ripe', label: 'Ripe', color: '#d84a3a' },
];

export default {
id: 'tomato-ripeness-by-season',
label: 'Tomato Ripeness',
group: 'Tomato Harvest Helper',
scope: 'image',

requires(schema) {
    return [
    'season',
    'parent0',
    'unripe_tomato_pixels',
    'midripe_tomato_pixels',
    'ripe_tomato_pixels',
    ].every(c => schema.allCols.includes(c));
},

async render(container, ctx) {
    container.style.width = '98%';
    const { andWhere } = ctx.sql;

    const rows = await ctx.queryRows(`
    SELECT
        "season" AS season,
        "parent0" AS growing_type,
        "unripe_tomato_pixels" AS unripe,
        "midripe_tomato_pixels" AS midripe,
        "ripe_tomato_pixels" AS ripe
    FROM pp_data
    ${andWhere(ctx.where, '"season" IS NOT NULL AND "parent0" IS NOT NULL')}
    `);

    if (!rows.length) {
    container.textContent = 'No tomato ripeness data available.';
    return;
    }

    const seasons = SEASON_ORDER.filter(s => rows.some(r => r.season === s));
    const growingTypes = ['greenhouse', 'outdoors'];
    const totals = new Map();

    // Sum tomato pixels for each season and growing environment.
    for (const row of rows) {
    const key = `${row.season}|${row.growing_type}`;

    if (!totals.has(key)) {
        totals.set(key, { unripe: 0, midripe: 0, ripe: 0 });
    }

    const total = totals.get(key);
    for (const { key: ripeness } of RIPENESS) {
        total[ripeness] += Number(row[ripeness]) || 0;
    }
    }

    // Greenhouse on the left, outdoors on the right.
    const positions = [];
    seasons.forEach((season, i) => {
    growingTypes.forEach((type, j) => {
        positions.push({
        season,
        type,
        x: i * 2 + (j === 0 ? -0.35 : 0.35),
        });
    });
    });

    const traces = RIPENESS.map(({ key, label, color }) => ({
    type: 'bar',
    name: label,
    x: positions.map(p => p.x),
    y: positions.map(p => {
        const values = totals.get(`${p.season}|${p.type}`);
        if (!values) return null;

        const sum = values.unripe + values.midripe + values.ripe;
        return sum > 0 ? 100 * values[key] / sum : 0;
    }),
    width: 0.55,
    marker: { color },
    customdata: positions.map(p => [p.season, p.type]),
    hovertemplate:
        '%{customdata[0]} / %{customdata[1]}<br>' +
        '%{fullData.name}: %{y:.1f}%<extra></extra>',
    }));

    Plotly.newPlot(container, traces, {
    title: { text: 'Tomato Ripeness by Season and Growing Environment' },
    height: 420,
    margin: { l: 60, r: 20, t: 50, b: 80 },
    barmode: 'stack',
    bargap: 0.15,
    xaxis: {
        title: '',
        tickmode: 'array',
        tickvals: seasons.flatMap((_, i) => [
        i * 2 - 0.35,
        i * 2 + 0.35,
        ]),
        ticktext: seasons.flatMap(() => ['Greenhouse', 'Outdoors']),
        range: [-1, (seasons.length - 1) * 2 + 1],
        zeroline: false,
    },
    annotations: seasons.map((season, i) => ({
        x: i * 2,
        y: -0.13,
        xref: 'x',
        yref: 'paper',
        text: season,
        showarrow: false,
        font: { size: 13 },
    })),
    yaxis: {
        title: 'Ripeness distribution (%)',
        range: [0, 100],
    },
    legend: { orientation: 'v' },
    }, { responsive: true });
},


    async overviewMessage(ctx) {
        const { andWhere } = ctx.sql;
        const rows = await ctx.queryRows(`
        SELECT
            "season" AS season,
            SUM("ripe_tomato_pixels") AS ripe,
            SUM("total_tomato_pixels") AS total
        FROM pp_data
        ${andWhere(ctx.where, '"season" IS NOT NULL AND "total_tomato_pixels" IS NOT NULL')}
        GROUP BY "season"
        `);

        if (!rows.length) return '';

        const shares = rows
        .filter(r => Number(r.total) > 0)
        .map(r => ({
            season: r.season,
            share: Number(r.ripe) / Number(r.total),
        }));

        if (!shares.length) return '';

        const top = shares.reduce((a, b) => b.share > a.share ? b : a);

        return `In <strong>${top.season}</strong>, most tomatoes are ripe.`;
    },


    async overviewPlot(container, ctx) {
    const { andWhere } = ctx.sql;

    const rows = await ctx.queryRows(`
    SELECT
    "season" AS season,
    "parent0" AS growing_type,
    "unripe_tomato_pixels" AS unripe,
    "midripe_tomato_pixels" AS midripe,
    "ripe_tomato_pixels" AS ripe
    FROM pp_data
    ${andWhere(ctx.where, '"season" IS NOT NULL AND "parent0" IS NOT NULL')}
    `);

    if (!rows.length) return false;

    const seasons = SEASON_ORDER.filter(s => rows.some(r => r.season === s));
    const growingTypes = ['greenhouse', 'outdoors'];
    const totals = new Map();

    for (const row of rows) {
    const key = `${row.season}|${row.growing_type}`;

    if (!totals.has(key)) {
    totals.set(key, { unripe: 0, midripe: 0, ripe: 0 });
    }

    const total = totals.get(key);
    for (const { key: ripeness } of RIPENESS) {
    total[ripeness] += Number(row[ripeness]) || 0;
    }
    }

    const positions = [];
    seasons.forEach((season, i) => {
    growingTypes.forEach((type, j) => {
    positions.push({
        season,
        type,
        x: i * 2 + (j === 0 ? -0.35 : 0.35),
    });
    });
    });

    const traces = RIPENESS.map(({ key, label, color }) => ({
    type: 'bar',
    name: label,
    x: positions.map(p => p.x),
    y: positions.map(p => {
    const values = totals.get(`${p.season}|${p.type}`);
    if (!values) return null;

    const sum = values.unripe + values.midripe + values.ripe;
    return sum > 0 ? 100 * values[key] / sum : 0;
    }),
    width: 0.55,
    marker: { color: '#3d7ea6' },
    }));

    ctx.plot.appendMini(container, traces, {
    barmode: 'stack',
    xaxis: {
    tickmode: 'array',
    tickvals: seasons.map((_, i) => i * 2),
    ticktext: seasons,
    range: [-1, (seasons.length - 1) * 2 + 1],
    zeroline: false,
    },
    yaxis: { range: [0, 100] },
    showlegend: false,
    });
    },
    };