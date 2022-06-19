function round_stock_value(num) {
	if (num <= 0.25) {
		return Math.round(num*1000) / 1000;
	} else if (num <= 0.5) {
		return Math.round(num*200) / 200;
	} else if (num <= 10) {
		return Math.round(num*100) / 100;
	} else if (num <= 20) {
		return Math.round(num*50) / 50;
	} else if (num <= 100) {
		return Math.round(num*20) / 20;
	} else if (num <= 200) {
		return Math.round(num*10) / 10;
	} else if (num <= 500) {
		return Math.round(num*5) / 5;
	} else if (num <= 1000) {
		return Math.round(num*2) / 2;
	} else if (num <= 2000) {
		return Math.round(num)
	} else if (num <= 5000) {
		return Math.round(num/2) * 2;
	} else {
		return Math.round(num/5) * 5;
	}
}

const line_chart_settings = {
	type: 'line',
	yAxisID: 'y',
	fill: false,
	borderWidth: 1,
	tension: 0.3,
	pointRadius: 0,
}

const x_scale_settings = {
	title: {
		display: false,
		text: 'Date'
	},
	type: 'timeseries',
	time: {
		unit: 'month',
		tooltipFormat: 'DD'
	},
	ticks: {
		autoSkip: true,
		autoSkipPadding: 80,
		maxRotation: 0,
		minRotation: 0
	}
}

const misc_options = {
	legend: {
		onClick: function (e) {
			e.stopPropagation();
		 }
	},
	interaction: {
		mode: 'index',
		intersect: false,
	},
	plugins: {
		/*zoom: {
			zoom: {
				wheel: {
					enabled: true
				},
				pinch: {
					enabled: true
				},
				mode: 'xy',
				onZoomComplete({chart}) {
					chart.update('none');
				}
			},
			pan: {
				enabled: true,
				mode: 'xy'
			}
		},*/
		title: {
			display: false
		},
		legend: {
			labels: {
				filter: function(item, chart) {
					if (item.text) {
						return item.text.length != 0;
					} else {
						return false;
					}
				}
			}
		},
		tooltip: {
			backgroundColor: "rgba(0, 0, 0, 0.5)",
			titleColor: "rgba(255, 255, 255, 0.7)",
			bodyColor: "rgba(255, 255, 255, 0.7)",
			callbacks: {
				label: function(context) {
					if (context.parsed.y != null && context.dataset.label) {
						if (['MA10', 'MA20', 'MA50', 'MA100', 'MA250'].includes(context.dataset.label)) { // MA labels
							return context.dataset.label + ': ' + round_stock_value(context.parsed.y);
						} else if (context.dataset.label == 'Volume') { // Volume label
							return "Volume: " + context.parsed.y.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ","); // thousand-separated commas
						} else if ($(context.chart.ctx.canvas).hasClass('comparison-chart')) { // comparison charts
							return context.dataset.label + ': ' + (100*context.parsed.y).toFixed(2) + '%'; // add %, round 2dp
						} else { // default
							return context.dataset.label + ': ' + context.parsed.y.toFixed(3); // default round 3dp
						}
					} else if (context.dataset.type == 'candlestick') {
						return 'O: ' + round_stock_value(context.parsed.o) +
							' / H: ' + round_stock_value(context.parsed.h) +
							' / L: ' + round_stock_value(context.parsed.l) +
							' / C: ' + round_stock_value(context.parsed.c);
					}
					return '';
				}
			}
		}
	},
	responsive: true,
	maintainAspectRatio: false
}

const crosshair_plugin = {
	id: 'crosshair',
	afterInit: (chart) => {
		chart.crosshair = {
			x: 0,
			y: 0
		}
	},
	afterEvent: (chart, evt) => {
		const {chartArea: {top, bottom, left, right}} = chart;
		const {event: {x, y}} = evt;
		chart.crosshair = {x, y, draw: !(x < left || x > right || y < top || y > bottom)}
		chart.draw();
	},
	afterDatasetsDraw: (chart, _, opts) => {
		if (!chart.crosshair) {
			return;
		}

		const {ctx, chartArea: {top, bottom, left, right}} = chart;
		const {x, y, draw} = chart.crosshair;

		if (!draw) {
			return;
		}

		ctx.lineWidth = opts.width || 2;
		ctx.setLineDash(opts.dash || [3, 3]);
		ctx.strokeStyle = opts.color || 'rgba(112, 110, 122, 0.6)'

		ctx.save();
		ctx.beginPath();
		ctx.moveTo(x, bottom);
		ctx.lineTo(x, top);
		ctx.moveTo(left, y);
		ctx.lineTo(right, y);
		ctx.stroke();
		ctx.restore();

		// reset line dash
		ctx.setLineDash([]);
	}
}

const cursorpos_plugin = {
	id: 'cursorpos',
	afterEvent: (chart, evt) => {
		const {chartArea: {top, bottom, left, right}} = chart;
		const {event: {x, y}} = evt;
		chart.cursorpos = {x, y, draw: !(x < left || x > right || y < top || y > bottom)}
		chart.draw();
	},
	afterDatasetsDraw: (chart, _, opts) => {
		if (!chart.cursorpos) {
			return;
		}

		const {ctx, chartArea: {top, bottom, left, right}} = chart;
		const {x, y, draw} = chart.cursorpos;
		if (!draw) {
			return;
		}

		ctx.font = '12px Arial';
		ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';

		x_val = new Date(chart.scales.x.getValueForPixel(x)).toISOString().slice(0, 10);
		y_val = chart.scales.y.getValueForPixel(y);

		if ($(chart.ctx.canvas).hasClass('comparison-chart')) {
			y_val = (y_val * 100).toFixed(2) + '%';
		} else {
			y_val = y_val.toFixed(3)
		}

		ctx.fillText('x: ' + x_val, left+5, top+10);
		ctx.fillText('y: ' + y_val, left+5, top+25);
	}
}

// enable plugins globally
Chart.register(crosshair_plugin)
Chart.register(cursorpos_plugin)