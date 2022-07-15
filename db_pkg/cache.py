from datetime import datetime, timedelta

from typing import Dict, List, Tuple
from bson import json_util
import pymongo
import json
from pprint import pprint
from . import stock, utils

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["wallstreetbeggars"]
col_cache = db["cache"]


def store_cached_result(fn_name, params, data):
	param_query = {"param_"+k: json.dumps(v, ensure_ascii=False, default=json_util.default) for k, v in params.items()}

	col_cache.delete_many({"fn_name": fn_name} | param_query)
	col_cache.insert_one({
		"fn_name": fn_name,
		"data": json.dumps(data, ensure_ascii=False, default=json_util.default)
	} | param_query)


def get_cached_result(fn_name, params):
	param_query = {"param_"+k: json.dumps(v, ensure_ascii=False, default=json_util.default) for k, v in params.items()}

	res = col_cache.find_one({"fn_name": fn_name} | param_query, {"_id": 0, "data": 1})
	if res is None: return None
	return json.loads(res["data"], object_hook=json_util.object_hook)


def clear_all_cache():
	col_cache.delete_many({})