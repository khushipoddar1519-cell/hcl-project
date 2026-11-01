/**
 * Hotel Analytics Visualization Engine
 * Clean, lightweight, self-contained SVG/Canvas charts.
 */
const Charts = {
  renderTrendChart(containerId, trendData) {
    const el = document.getElementById(containerId);
    if (!el || !trendData || trendData.length === 0) return;

    const width = el.clientWidth || 600;
    const height = 300;
    const pad = { top: 20, right: 30, bottom: 40, left: 55 };
    const chartW = width - pad.left - pad.right;
    const chartH = height - pad.top - pad.bottom;

    const maxBookings = Math.max(...trendData.map(d => d.bookings), 10);
    const n = trendData.length;
    const barW = Math.max(chartW / n - 4, 3);

    let barsSvg = '';
    let linePoints = [];
    let xLabels = '';

    trendData.forEach((d, i) => {
      const x = pad.left + i * (chartW / n) + 2;
      const bH = (d.bookings / maxBookings) * chartH;
      const bY = pad.top + chartH - bH;

      const cY = pad.top + chartH - (d.cancelled / maxBookings) * chartH;
      const cX = x + barW / 2;
      linePoints.push(`${cX},${cY}`);

      // Bookings bar
      barsSvg += `
        <rect x="${x}" y="${bY}" width="${barW}" height="${bH}" rx="3" fill="#3b82f6" opacity="0.85">
          <title>${d.month}: ${d.bookings.toLocaleString()} Bookings</title>
        </rect>
      `;

      // Label every 3-4 months to avoid clutter
      if (i % Math.ceil(n / 8) === 0 || i === n - 1) {
        xLabels += `<text x="${x + barW/2}" y="${height - 12}" fill="#64748b" font-size="11" text-anchor="middle">${d.month}</text>`;
      }
    });

    const pathD = `M ` + linePoints.join(' L ');
    let cancelDots = '';
    trendData.forEach((d, i) => {
      const parts = linePoints[i].split(',');
      cancelDots += `
        <circle cx="${parts[0]}" cy="${parts[1]}" r="4" fill="#f43f5e" stroke="#0b1329" stroke-width="2">
          <title>${d.month}: ${d.cancelled.toLocaleString()} Cancellations (${d.cancel_rate}%)</title>
        </circle>
      `;
    });

    // Horizontal grid lines
    let gridSvg = '';
    for (let step = 0; step <= 4; step++) {
      const val = Math.round((maxBookings / 4) * step);
      const y = pad.top + chartH - (step / 4) * chartH;
      gridSvg += `
        <line x1="${pad.left}" y1="${y}" x2="${width - pad.right}" y2="${y}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3,3" />
        <text x="${pad.left - 10}" y="${y + 4}" fill="#64748b" font-size="10" text-anchor="end">${val.toLocaleString()}</text>
      `;
    }

    el.innerHTML = `
      <div style="display:flex; justify-content:flex-end; gap:16px; font-size:12px; margin-bottom:10px;">
        <span style="display:inline-flex; align-items:center; gap:6px;"><span style="width:10px; height:10px; background:#3b82f6; border-radius:2px;"></span> Bookings</span>
        <span style="display:inline-flex; align-items:center; gap:6px;"><span style="width:10px; height:10px; background:#f43f5e; border-radius:50%;"></span> Cancellations</span>
      </div>
      <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" style="overflow:visible;">
        ${gridSvg}
        ${barsSvg}
        <path d="${pathD}" fill="none" stroke="#f43f5e" stroke-width="2.5" />
        ${cancelDots}
        ${xLabels}
      </svg>
    `;
  },

  renderRoomDonut(containerId, roomsData) {
    const el = document.getElementById(containerId);
    if (!el || !roomsData || roomsData.length === 0) return;

    const totalRev = roomsData.reduce((acc, r) => acc + r.revenue, 0);
    const size = 220;
    const center = size / 2;
    const radius = 80;
    const strokeWidth = 28;

    let startAngle = 0;
    let paths = '';

    roomsData.forEach(r => {
      const share = totalRev > 0 ? r.revenue / totalRev : 0;
      const angle = share * 360;
      const endAngle = startAngle + angle;

      const x1 = center + radius * Math.cos((Math.PI * (startAngle - 90)) / 180);
      const y1 = center + radius * Math.sin((Math.PI * (startAngle - 90)) / 180);
      const x2 = center + radius * Math.cos((Math.PI * (endAngle - 90)) / 180);
      const y2 = center + radius * Math.sin((Math.PI * (endAngle - 90)) / 180);

      const largeArc = angle > 180 ? 1 : 0;
      const d = `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`;

      paths += `
        <path d="${d}" fill="none" stroke="${r.color || '#7c6cf0'}" stroke-width="${strokeWidth}" stroke-linecap="round">
          <title>${r.room_group}: ${r.revenue_formatted} (${r.revenue_share}%)</title>
        </path>
      `;
      startAngle = endAngle;
    });

    let legendHtml = roomsData.map(r => `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; font-size:12px;">
        <span style="display:inline-flex; align-items:center; gap:8px;">
          <span style="width:10px; height:10px; border-radius:50%; background:${r.color};"></span>
          <span>${r.room_group}</span>
        </span>
        <span style="font-weight:600;">${r.revenue_share}%</span>
      </div>
    `).join('');

    el.innerHTML = `
      <div style="display:flex; align-items:center; gap:24px; flex-wrap:wrap;">
        <div style="position:relative; width:${size}px; height:${size}px; margin:0 auto;">
          <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
            ${paths}
          </svg>
          <div style="position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; pointer-events:none;">
            <span style="font-size:11px; color:#94a3b8; text-transform:uppercase;">Total Share</span>
            <span style="font-size:18px; font-weight:700; color:#fff;">100%</span>
          </div>
        </div>
        <div style="flex:1; min-width:140px;">
          ${legendHtml}
        </div>
      </div>
    `;
  },

  renderForecastChart(containerId, forecastData) {
    const el = document.getElementById(containerId);
    if (!el || !forecastData || !forecastData.points) return;

    const points = forecastData.points;
    const width = el.clientWidth || 600;
    const height = 300;
    const pad = { top: 20, right: 30, bottom: 40, left: 60 };
    const chartW = width - pad.left - pad.right;
    const chartH = height - pad.top - pad.bottom;

    const allVals = points.flatMap(p => [p.actual, p.forecast, p.upper, p.lower].filter(v => v !== null));
    const maxVal = Math.max(...allVals, 10) * 1.1;
    const minVal = Math.max(0, Math.min(...allVals) * 0.85);

    const n = points.length;
    const stepX = chartW / (n - 1);

    let actualPoints = [];
    let fcPoints = [];
    let upperPoints = [];
    let lowerPoints = [];
    let xLabels = '';

    points.forEach((p, i) => {
      const x = pad.left + i * stepX;
      xLabels += `<text x="${x}" y="${height - 12}" fill="#64748b" font-size="11" text-anchor="middle">${p.month}</text>`;

      if (p.actual !== null) {
        const y = pad.top + chartH - ((p.actual - minVal) / (maxVal - minVal)) * chartH;
        actualPoints.push(`${x},${y}`);
      }

      if (p.forecast !== null) {
        const y = pad.top + chartH - ((p.forecast - minVal) / (maxVal - minVal)) * chartH;
        fcPoints.push(`${x},${y}`);

        const yUp = pad.top + chartH - ((p.upper - minVal) / (maxVal - minVal)) * chartH;
        const yLow = pad.top + chartH - ((p.lower - minVal) / (maxVal - minVal)) * chartH;
        upperPoints.push(`${x},${yUp}`);
        lowerPoints.unshift(`${x},${yLow}`);
      }
    });

    // Bridge actual and forecast
    if (actualPoints.length && fcPoints.length) {
      fcPoints.unshift(actualPoints[actualPoints.length - 1]);
      upperPoints.unshift(actualPoints[actualPoints.length - 1]);
      lowerPoints.push(actualPoints[actualPoints.length - 1]);
    }

    const bandPath = upperPoints.length ? `M ` + upperPoints.join(' L ') + ` L ` + lowerPoints.join(' L ') + ` Z` : '';
    const actualPath = actualPoints.length ? `M ` + actualPoints.join(' L ') : '';
    const fcPath = fcPoints.length ? `M ` + fcPoints.join(' L ') : '';

    el.innerHTML = `
      <div style="display:flex; justify-content:flex-end; gap:16px; font-size:12px; margin-bottom:10px;">
        <span style="display:inline-flex; align-items:center; gap:6px;"><span style="width:10px; height:10px; background:#3b82f6; border-radius:50%;"></span> Actual History</span>
        <span style="display:inline-flex; align-items:center; gap:6px;"><span style="width:10px; height:10px; background:#8b5cf6; border-radius:50%;"></span> Forecast</span>
        <span style="display:inline-flex; align-items:center; gap:6px;"><span style="width:12px; height:8px; background:rgba(139,92,246,0.2); border-radius:2px;"></span> 80% Confidence Band</span>
      </div>
      <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" style="overflow:visible;">
        ${bandPath ? `<path d="${bandPath}" fill="rgba(139, 92, 246, 0.18)" />` : ''}
        ${actualPath ? `<path d="${actualPath}" fill="none" stroke="#3b82f6" stroke-width="3" />` : ''}
        ${fcPath ? `<path d="${fcPath}" fill="none" stroke="#8b5cf6" stroke-width="3" stroke-dasharray="5,4" />` : ''}
        ${points.map((p, i) => {
          const x = pad.left + i * stepX;
          if (p.actual !== null) {
            const y = pad.top + chartH - ((p.actual - minVal) / (maxVal - minVal)) * chartH;
            return `<circle cx="${x}" cy="${y}" r="4" fill="#3b82f6" stroke="#0b1329" stroke-width="2"><title>${p.month} (Actual): ${p.actual.toLocaleString()}</title></circle>`;
          }
          if (p.forecast !== null) {
            const y = pad.top + chartH - ((p.forecast - minVal) / (maxVal - minVal)) * chartH;
            return `<circle cx="${x}" cy="${y}" r="4.5" fill="#8b5cf6" stroke="#0b1329" stroke-width="2"><title>${p.month} (Forecast): ${p.forecast.toLocaleString()} (Range: ${p.lower.toLocaleString()} - ${p.upper.toLocaleString()})</title></circle>`;
          }
          return '';
        }).join('')}
        ${xLabels}
      </svg>
    `;
  },

  renderGauge(containerId, pct, riskLevel) {
    const el = document.getElementById(containerId);
    if (!el) return;

    let color = '#10b981';
    if (riskLevel === 'Medium') color = '#f59e0b';
    if (riskLevel === 'High') color = '#f43f5e';

    const r = 70;
    const circ = Math.PI * r; // half circle perimeter
    const offset = circ - (pct / 100) * circ;

    el.innerHTML = `
      <div class="gauge-svg-wrap">
        <svg width="220" height="120" viewBox="0 0 200 110">
          <path d="M 20 100 A 70 70 0 0 1 180 100" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="16" stroke-linecap="round" />
          <path d="M 20 100 A 70 70 0 0 1 180 100" fill="none" stroke="${color}" stroke-width="16" stroke-linecap="round"
                stroke-dasharray="${circ}" stroke-dashoffset="${offset}" style="transition: stroke-dashoffset 0.6s ease, stroke 0.4s ease;" />
        </svg>
        <div class="gauge-score-display">
          <div class="gauge-pct" style="color: ${color};">${pct}%</div>
          <div class="gauge-sub">Cancellation Probability</div>
        </div>
      </div>
    `;
  },

  renderDrivers(containerId, drivers) {
    const el = document.getElementById(containerId);
    if (!el || !drivers) return;

    const maxImp = Math.max(...drivers.map(d => Math.abs(d.impact)), 1);

    el.innerHTML = drivers.map(d => {
      const isPositive = d.impact > 0;
      const widthPct = Math.min((Math.abs(d.impact) / maxImp) * 100, 100);
      const color = isPositive ? '#f43f5e' : '#10b981';
      const sign = isPositive ? '+' : '';

      return `
        <div class="driver-bar-item">
          <div class="driver-bar-header">
            <span>${d.feature}</span>
            <span style="color:${color}; font-weight:600;">${sign}${d.impact}%</span>
          </div>
          <div class="driver-track">
            <div class="driver-fill" style="width:${widthPct}%; background:${color};"></div>
          </div>
        </div>
      `;
    }).join('');
  }
};

window.Charts = Charts;

