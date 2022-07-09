from datetime import datetime, timedelta


def get_datetime_from_period(period):
	end_datetime = datetime.now()
	start_datetime = end_datetime - timedelta(days=period)
	return start_datetime, end_datetime
	

def format_rules(hit_buy_rules, hit_sell_rules, miss_buy_rules, miss_sell_rules):
	indicators_map = {
		"sma10": "MA10",
		"sma20": "MA20",
		"sma50": "MA50",
		"sma100": "MA100",
		"sma250": "MA250",
		"rsi": "RSI"
	}

	f_hit_buy_rules = []
	for var1, op, var2 in hit_buy_rules:
		var1 = indicators_map[var1] if not isinstance(var1, int) else var1
		var2 = indicators_map[var2] if not isinstance(var2, int) else var2
		f_hit_buy_rules.append(f"{var1} {op} {var2}")

	f_hit_sell_rules = []
	for var1, op, var2 in hit_sell_rules:
		var1 = indicators_map[var1] if not isinstance(var1, int) else var1
		var2 = indicators_map[var2] if not isinstance(var2, int) else var2
		f_hit_sell_rules.append(f"{var1} {op} {var2}")

	f_miss_buy_rules = []
	for var1, op, var2 in miss_buy_rules:
		var1 = indicators_map[var1] if not isinstance(var1, int) else var1
		var2 = indicators_map[var2] if not isinstance(var2, int) else var2
		f_miss_buy_rules.append(f"{var1} {op} {var2}")

	f_miss_sell_rules = []
	for var1, op, var2 in miss_sell_rules:
		var1 = indicators_map[var1] if not isinstance(var1, int) else var1
		var2 = indicators_map[var2] if not isinstance(var2, int) else var2
		f_miss_sell_rules.append(f"{var1} {op} {var2}")
	
	return f_hit_buy_rules, f_hit_sell_rules, f_miss_buy_rules, f_miss_sell_rules


def get_hit_miss_rules(data, parsed_buy_rules, parsed_sell_rules):
	hit_buy_rules, hit_sell_rules, miss_buy_rules, miss_sell_rules = [], [], [], []
	for rule in parsed_buy_rules:
		var1, op, var2 = rule
		if not isinstance(var1, int): var1 = data[var1]
		if not isinstance(var2, int): var2 = data[var2]

		if (op == "≤" and var1 <= var2) or (op == "≥" and var1 >= var2):
			hit_buy_rules.append(rule)
		else:
			miss_buy_rules.append(rule)

	for rule in parsed_sell_rules:
		var1, op, var2 = rule
		if not isinstance(var1, int): var1 = data[var1]
		if not isinstance(var2, int): var2 = data[var2]

		if (op == "≤" and var1 <= var2) or (op == "≥" and var1 >= var2):
			hit_sell_rules.append(rule)
		else:
			miss_sell_rules.append(rule)
	
	return hit_buy_rules, hit_sell_rules, miss_buy_rules, miss_sell_rules


def parse_rules(buy_rules, sell_rules):
	indicators_map = {
		"MA10": "sma10",
		"MA20": "sma20",
		"MA50": "sma50",
		"MA100": "sma100",
		"MA250": "sma250",
		"RSI": "rsi"
	}
	parsed_buy_rules, parsed_sell_rules = [], []

	for rule in buy_rules:
		var1, op, var2 = rule.split(" ")
		var1 = indicators_map[var1] if var1 in indicators_map.keys() else int(var1)
		var2 = indicators_map[var2] if var2 in indicators_map.keys() else int(var2)
		parsed_buy_rules.append([var1, op, var2])
	
	for rule in sell_rules:
		var1, op, var2 = rule.split(" ")
		var1 = indicators_map[var1] if var1 in indicators_map.keys() else int(var1)
		var2 = indicators_map[var2] if var2 in indicators_map.keys() else int(var2)
		parsed_sell_rules.append([var1, op, var2])

	return parsed_buy_rules, parsed_sell_rules