from datetime import datetime, timedelta


def get_datetime_from_period(period):
	end_datetime = datetime.now()
	start_datetime = end_datetime - timedelta(days=period)
	return start_datetime, end_datetime


def get_pagination_btns(page, max_page):
	if max_page <= 5:
		return [str(i) for i in range(1, max_page+1)]
	else:
		if page <= 3:
			return [str(i) for i in range(1, page+2)] + ["...", str(max_page)]
		elif page >= max_page - 2:
			return ["1", "..."] + [str(i) for i in range(page-1, max_page+1)]
		else:
			return ["1", "...", str(page-1), str(page), str(page+1), "...", str(max_page)]


def format_rules(hit_buy_rules, hit_sell_rules, miss_buy_rules, miss_sell_rules):
	indicators_map = {
		"sma10": "MA10", "sma20": "MA20", "sma50": "MA50", "sma100": "MA100", "sma250": "MA250",
		"rsi": "RSI", "macd": "MACD", "macd_ema": "EMA", "macd_div": "MACD(div)",
		"close": "Close", "close_pct": "Change",
		"stoch_slowk": "Stoch(slow,%k)", "stoch_slowd": "Stoch(slow,%d)",
		"stoch_fastk": "Stoch(fast,%k)", "stoch_fastd": "Stoch(fast,%d)"
	}

	f_hit_buy_rules = []
	for var1, op, var2 in hit_buy_rules:
		var1 = indicators_map[var1] if not isinstance(var1, (int, float)) else var1
		var2 = indicators_map[var2] if not isinstance(var2, (int, float)) else var2
		f_hit_buy_rules.append(f"{var1} {op} {var2}")

	f_hit_sell_rules = []
	for var1, op, var2 in hit_sell_rules:
		var1 = indicators_map[var1] if not isinstance(var1, (int, float)) else var1
		var2 = indicators_map[var2] if not isinstance(var2, (int, float)) else var2
		f_hit_sell_rules.append(f"{var1} {op} {var2}")

	f_miss_buy_rules = []
	for var1, op, var2 in miss_buy_rules:
		var1 = indicators_map[var1] if not isinstance(var1, (int, float)) else var1
		var2 = indicators_map[var2] if not isinstance(var2, (int, float)) else var2
		f_miss_buy_rules.append(f"{var1} {op} {var2}")

	f_miss_sell_rules = []
	for var1, op, var2 in miss_sell_rules:
		var1 = indicators_map[var1] if not isinstance(var1, (int, float)) else var1
		var2 = indicators_map[var2] if not isinstance(var2, (int, float)) else var2
		f_miss_sell_rules.append(f"{var1} {op} {var2}")
	
	return f_hit_buy_rules, f_hit_sell_rules, f_miss_buy_rules, f_miss_sell_rules


def get_hit_miss_rules(data, parsed_buy_rules, parsed_sell_rules):
	hit_buy_rules, hit_sell_rules, miss_buy_rules, miss_sell_rules = [], [], [], []
	for rule in parsed_buy_rules:
		var1, op, var2 = rule
		if not isinstance(var1, (int, float)): var1 = data[var1]
		if not isinstance(var2, (int, float)): var2 = data[var2]

		if (op == "≤" and var1 <= var2) or (op == "≥" and var1 >= var2):
			hit_buy_rules.append(rule)
		else:
			miss_buy_rules.append(rule)

	for rule in parsed_sell_rules:
		var1, op, var2 = rule
		if not isinstance(var1, (int, float)): var1 = data[var1]
		if not isinstance(var2, (int, float)): var2 = data[var2]

		if (op == "≤" and var1 <= var2) or (op == "≥" and var1 >= var2):
			hit_sell_rules.append(rule)
		else:
			miss_sell_rules.append(rule)
	
	return hit_buy_rules, hit_sell_rules, miss_buy_rules, miss_sell_rules


def parse_rules(buy_rules, sell_rules):
	indicators_map = {
		"MA10": "sma10", "MA20": "sma20", "MA50": "sma50", "MA100": "sma100", "MA250": "sma250",
		"RSI": "rsi", "MACD": "macd", "EMA": "macd_ema", "MACD(div)": "macd_div",
		"Close": "close", "Change": "close_pct",
		"Stoch(slow,%k)": "stoch_slowk", "Stoch(slow,%d)": "stoch_slowd",
		"Stoch(fast,%k)": "stoch_fastk", "Stoch(fast,%d)": "stoch_fastd"
	}
	parsed_buy_rules, parsed_sell_rules = [], []

	def _int(num_str):
		if float(num_str) % 1 == 0:
			return int(num_str)
		else:
			return float(num_str)

	for rule in buy_rules:
		var1, op, var2 = rule.split(" ")
		var1 = indicators_map[var1] if var1 in indicators_map.keys() else _int(var1)
		var2 = indicators_map[var2] if var2 in indicators_map.keys() else _int(var2)
		parsed_buy_rules.append([var1, op, var2])
	
	for rule in sell_rules:
		var1, op, var2 = rule.split(" ")
		var1 = indicators_map[var1] if var1 in indicators_map.keys() else _int(var1)
		var2 = indicators_map[var2] if var2 in indicators_map.keys() else _int(var2)
		parsed_sell_rules.append([var1, op, var2])

	return parsed_buy_rules, parsed_sell_rules