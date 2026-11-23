/**
 * Tomato Pixels by Season plugin - part of the Tomato Harvest Helper Extension.
 *
 * Plots the total_tomato_pixels computed by TomatoRipenessProcessor (from the
 * actual pixel data) against the season metadata read from the PNG images,
 * split and colored by growing environment (greenhouse or outdoors), just
 * like the built-in widgets. A scatter plot is used rather than a box/violin
 * plot because each season contains only a handful of observations.
 * 
 * Load via the extension manifest (recommended):
 *   ?extension=https://your-host/extension.json
 *
 * Or standalone:
 *   ?plugin=https://your-host/plugin_dives_logged.js
 */
 

const SEASON_ORDER = ['spring', 'summer', 'autumn', 'winter'];

export default {
  id: 'tomato-by-season',
  label: 'Tomato Coverage',
  group: 'Tomato Harvest Helper',
  scope: 'image',

  requires(schema) {
    return ['season', 'total_tomato_pixels'].every(c => schema.allCols.includes(c));
  },

  async render(container, ctx) {
    container.style.width = '98%';
    container.style.maxWidth = '100%';
    container.style.minWidth = '0';
    const { andWhere } = ctx.sql;
    const rows = await ctx.queryRows(`
      SELECT
        "season"              AS season,
        "parent0"             AS growing_type,
        "total_tomato_pixels" AS tomato_pixels
      FROM pp_data
      ${andWhere(ctx.where, '"season" IS NOT NULL AND "total_tomato_pixels" IS NOT NULL')}
    `);

    if (!rows.length) {
      container.textContent = 'No tomato harvest data available.';
      return;
    }

    const seasons = SEASON_ORDER.filter(s => rows.some(r => r.season === s));
    const growingTypes = [...new Set(rows.map(r => r.growing_type))].sort();

    Plotly.newPlot(container, growingTypes.map(type => {
      const sub = rows.filter(r => r.growing_type === type);
      return {
        type: 'scatter',
        mode: 'markers',
        name: type,
        x: sub.map(r => seasons.indexOf(r.season) + (type === 'greenhouse' ? -0.08 : 0.08)),
        y: sub.map(r => Number(r.tomato_pixels)),
        text: sub.map(r => r.season),
        hovertemplate: '%{text}: %{y} tomato pixels<extra>%{fullData.name}</extra>',
        marker: { size: 12, color: ctx.colorMap[type] ?? '#888' },
      };
    }), {
      title: { text: 'How does tomato coverage vary across seasons?' },
      height: 420,
      margin: { l: 60, r: 20, t: 50, b: 60 },
      xaxis: {
        title: 'Season',
        tickmode: 'array',
        tickvals: seasons.map((_, i) => i),
        ticktext: seasons,
        range: [-0.5, seasons.length - 0.5],
        zeroline: false
      },
      yaxis: { title: 'Tomato coverage (pixels)', rangemode: 'tozero' },
    }, { responsive: true });
  },

  // Shown on the widget's tile in Overview mode (the default tile-gallery view).

  async overviewMessage(ctx) {
    const { andWhere } = ctx.sql;
    const rows = await ctx.queryRows(`
      SELECT "season" AS season, AVG("total_tomato_pixels") AS avg_pixels
      FROM pp_data
      ${andWhere(ctx.where, '"season" IS NOT NULL AND "total_tomato_pixels" IS NOT NULL')}
      GROUP BY 1
    `);
    if (!rows.length) return null;
    const top = rows.reduce((a, b) => (Number(b.avg_pixels) > Number(a.avg_pixels) ? b : a));
    return `<strong>${top.season.charAt(0).toUpperCase() + top.season.slice(1)}</strong> has the most tomatoes.`;
  },

  async overviewPlot(container, ctx) {
    const { andWhere } = ctx.sql;
    const rows = await ctx.queryRows(`
      SELECT "season" AS season, "parent0" AS growing_type, "total_tomato_pixels" AS tomato_pixels
      FROM pp_data
      ${andWhere(ctx.where, '"season" IS NOT NULL AND "total_tomato_pixels" IS NOT NULL')}
    `);
    if (!rows.length) return false;

    const seasons = SEASON_ORDER.filter(s => rows.some(r => r.season === s));
    ctx.plot.appendMini(container, [{
      type: 'scatter',
      mode: 'markers',
      x: rows.map(r => seasons.indexOf(r.season) + (r.growing_type === 'greenhouse' ? -0.1 : 0.1)),
      y: rows.map(r => Number(r.tomato_pixels)),
      marker: { size: 8, color: '#3d7ea6' },
    }], {
      xaxis: {
        tickmode: 'array',
        tickvals: seasons.map((_, i) => i),
        ticktext: seasons,
        range: [-0.5, seasons.length - 0.5],
      },
    });
  },
};