from datetime import datetime, timedelta

from typing import Dict, List, Tuple
from bson import json_util
import pymongo
import json
from pprint import pprint
from . import stock, utils

client = pymongo.MongoClient("mongodb+srv://root:test1234@wallstreetbeggars.auo5igi.mongodb.net/?retryWrites=true&w=majority")
db = client["wallstreetbeggars"]
col_cache = db["cache"]


def store_cached_result(fn_name, params, data):
	param_query = {"param_"+k: json.dumps(v, ensure_ascii=False, default=json_util.default) for k, v in params.items()}

	col_cache.delete_many({"fn_name": fn_name} | param_query)
	col_cache.insert_one({
		"fn_name": fn_name,
		"date": datetime.timestamp(datetime.now()),
		"data": json.dumps(data, ensure_ascii=False, default=json_util.default)
	} | param_query)


def get_cached_result(fn_name, params, period=1):
	param_query = {"param_"+k: json.dumps(v, ensure_ascii=False, default=json_util.default) for k, v in params.items()}
	min_date = datetime.timestamp(datetime.now() - timedelta(days=period))
	res = list(col_cache\
		.find({"fn_name": fn_name, "date": {"$gte": min_date}} | param_query, {"_id": 0, "data": 1})\
		.sort([("date", pymongo.DESCENDING)])\
		.limit(1))
	if len(res) == 0: return None
	return json.loads(res[0]["data"], object_hook=json_util.object_hook)


def clear_all_cache():
	col_cache.delete_many({})