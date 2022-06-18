from datetime import datetime, timedelta

def get_datetime_from_period(period):
	end_datetime = datetime.now()
	start_datetime = end_datetime - timedelta(days=period)
	return start_datetime, end_datetime


def process_industry_avg(data, interval=1):
	out = {
		'close_pct': []
	}

	c = -1
	for date, close_pct in data.items():
		c += 1
		if c % interval != 0:
			continue

		out['close_pct'].append({
			'x': datetime.timestamp(date) * 1000, # epoch in milliseconds
			'y': sum(close_pct) / len(close_pct)
		})

	return out


def process_stock_data(data, interval=1, include=[], precision=4):
	out = {
		'sma10': [], 'sma20': [], 'sma50': [], 'sma100': [], 'sma250': [],
		'macd': [], 'macd_ema': [], 'macd_div': [], 'rsi': [],
		'cdl': [],
		'close': [], 'close_pct': [],
		'volume': [], 'volume_color': []
	}
	max_volume = 0
	first_close = None
	
	volume_up_color = 'rgba(215,85,65,0.4)'
	volume_dn_color = 'rgba(80,160,115,0.4)'
	
	for c, i in enumerate(data):
		if c % interval != 0:
			continue

		if i['volume'] > max_volume:
			max_volume = i['volume']

		if first_close is None:
			first_close = i['close']

		out['cdl'].append({
			'x': int(datetime.timestamp(i['date']) * 1000),
			'o': round(i['open'], precision),
			'h': round(i['high'], precision),
			'l': round(i['low'], precision),
			'c': round(i['close'], precision)
		})

		for col in ['sma10', 'sma20', 'sma50', 'sma100', 'sma250', 'rsi', 'macd', 'macd_div', 'macd_ema', 'volume', 'close']:
			out[col].append({
				'x': int(datetime.timestamp(i['date']) * 1000),
				'y': round(i[col], precision)
			})

		out['close_pct'].append({
			'x': int(datetime.timestamp(i['date']) * 1000),
			'y': round((i['close'] - first_close) / first_close, precision)
		})

		if i['open'] > i['close']:
			out['volume_color'].append(volume_up_color)
		else:
			out['volume_color'].append(volume_dn_color)

		out['last_close'] = round(i['close'], precision)

	out['last_close_pct'] = round(100 * (out['close'][-1]['y'] - out['close'][-2]['y']) / out['close'][-2]['y'], precision)
	out['max_volume'] = max_volume

	if len(include) != 0:
		return dict(filter(lambda k: k[0] in include, out.items()))

	return out