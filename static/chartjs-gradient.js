async function draw_stock_cmp(data, other_ticker) {
	await $.get('/api/close', {
		ticker: other_ticker,
	}, function(res) {
		other_data = res
	});

	console.log(other_data);

	gradient1 = stock_cmp_ctx.createLinearGradient(0, 0, 0, 300);
	gradient1.addColorStop(0, 'rgba(255, 43, 43, 0.8)');
	gradient1.addColorStop(1, 'rgba(255, 43, 43, 0.1)');

	gradient2 = stock_cmp_ctx.createLinearGradient(0, 0, 0, 300);
	gradient2.addColorStop(0, 'rgba(43, 43, 255, 0.8)');
	gradient2.addColorStop(1, 'rgba(43, 43, 255, 0.1)');

	options = {
		tension: 0.3,
		pointRadius: 0,
		legend: {
			onClick: function (e) {
				e.stopPropagation();
			}
		},
		scales: {
			x: {
				display: false,
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
					text: 'Dollars (HKD)'
				},
				position: 'right',
				grid: {
					drawOnChartArea: false
				},
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
		maintainAspectRatio: false,
	}

	chart_data = {
		labels: data.lbl,
		datasets: [{
			label: 'Close 1',
			type: 'line',
			data: data.close,
			backgroundColor: gradient1,
			yAxisID: 'y',
			fill: true
		}, {
			label: 'Close 2',
			type: 'line',
			data: other_data.close,
			backgroundColor: gradient2,
			fill: true,
			yAxisID: 'y1'
		}],
	}

	if (stock_cmp_chart) {
		stock_cmp_chart.destroy();
	}

	stock_cmp_chart = new Chart(stock_cmp_ctx, {
		type: 'line',
		data: chart_data,
		options: options
	});
}