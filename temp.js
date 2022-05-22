var cdl_chart = undefined;
var rsi_chart = undefined;
var macd_chart = undefined;

const cdl_ctx = document.getElementById('cdl_chart').getContext('2d');
const rsi_ctx = document.getElementById('rsi_chart').getContext('2d');
const macd_ctx = document.getElementById('macd_chart').getContext('2d');

const line_chart_settings = {
	type: 'line',
	yAxisID: 'y',
	fill: false,
	borderWidth: 1,
	tension: 0.1,
	pointRadius: 0,
}

function draw_cdl(data) {
	chart_data = {
		labels: data.lbl,
		datasets: [{
			label: 'Candlestick',
			type: 'candlestick',
			data: data.cdl,
			yAxisID: 'y'
		}, {
			label: 'MA10',
			data: data.sma10,
			borderColor: 'rgb(174, 32, 18)',
			...line_chart_settings
		}, {
			label: 'MA20',
			data: data.sma20,
			borderColor: 'rgb(202, 103, 2)',
			...line_chart_settings
		}, {
			label: 'MA50',
			data: data.sma50,
			borderColor: 'rgb(238, 155, 0)',
			...line_chart_settings
		}, {
			label: 'Volume',
			type: 'bar',
			data: data.volume,
			backgroundColor: data.vol_color,
			yAxisID: 'y1'
		}]
	}

	options = {
		legend: {
			onClick: function (e) {
				e.stopPropagation();
			}
		},
		scales: {
			x: {
				display: true,
				title: {
					display: false,
					text: 'Date'
				},
				type: 'timeseries',
				time: {
					unit: 'month'
				}
			},
			y: {
				display: true,
				title: {
					display: false,
					text: 'Dollars (HKD)'
				}
			},
			y1: {
				display: true,
				title: {
					display: false,
					text: 'Volume (HKD)'
				},
				position: 'right',
				min: 0,
				max: data.max_vol.toPrecision(2) * 4,
				grid: {
					drawOnChartArea: false
				},
				ticks: {
					callback: (val) => (val.toExponential())
				}
			}
		},
		interaction: {
			mode: '',
			intersect: true
		},
		plugins: {
			title: {
				display: false
			}
		},
		responsive: true,
		maintainAspectRatio: true,
	}

	if (cdl_chart) {
		cdl_chart.destroy();
	}

	cdl_chart = new Chart(cdl_ctx, {
		type: 'candlestick',
		data: cdl_chart_data,
		options: cdl_options
	});
}

function draw_rsi(data) {
	chart_data = {
		labels: data.lbl,
		datasets: [{
			label: 'RSI',
			data: data.rsi,
			...line_chart_settings
		}]
	}

	options = {
		legend: {
			onClick: function (e) {
				e.stopPropagation();
			}
		},
		scales: {
			x: {
				display: true,
				title: {
					display: false,
					text: 'Date'
				},
				type: 'timeseries',
				time: {
					unit: 'month'
				}
			},
			y: {
				display: true,
				title: {
					display: false,
					text: 'Dollars (HKD)'
				}
			}
		},
		interaction: {
			mode: '',
			intersect: true
		},
		plugins: {
			title: {
				display: false
			}
		},
		responsive: true,
		maintainAspectRatio: true,
	}

	if (rsi_chart) {
		rsi_chart.destroy();
	}

	rsi_chart = new Chart(rsi_ctx, {
		type: 'line',
		data: rsi_chart_data,
		options: rsi_options
	});

	
}

function draw_macd(data) {
	chart_data = {
		labels: data.lbl,
		datasets: [{
			label: 'MACD',
			data: data.macd,
			...line_chart_settings
		}, {
			label: 'MACD EMA',
			data: data.macd_ema,
			...line_chart_settings
		}, {
			label: 'Divergence',
			type: 'bar',
			data: data.macd_div,
		}]
	}

	options = {
		legend: {
			onClick: function (e) {
				e.stopPropagation();
			}
		},
		scales: {
			x: {
				display: true,
				title: {
					display: false,
					text: 'Date'
				},
				type: 'timeseries',
				time: {
					unit: 'month'
				}
			},
			y: {
				display: true,
				title: {
					display: false,
					text: 'Dollars (HKD)'
				}
			}
		},
		interaction: {
			mode: '',
			intersect: true
		},
		plugins: {
			title: {
				display: false
			}
		},
		responsive: true,
		maintainAspectRatio: true,
	}

	if (macd_chart) {
		macd_chart.destroy();
	}

	macd_chart = new Chart(macd_ctx, {
		type: 'line',
		data: macd_chart_data,
		options: macd_options
	});
}

function draw_charts(data) {
	console.log(data);

	draw_cdl(data);
	draw_rsi(data);
	draw_macd(data);
}

draw_charts({{ data | tojson }})