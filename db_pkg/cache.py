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
	col_cache.delete_many({"fn_name": fn_name} | {"param_"+k: v for k, v in params.items()})

	col_cache.insert_one({
		"fn_name": fn_name,
		"data": json.dumps(data, ensure_ascii=False, default=json_util.default)
	} | {"param_"+k: v for k, v in params.items()})


def get_cached_result(fn_name, params):
	res = col_cache.find_one({"fn_name": fn_name} | {"param_"+k: v for k, v in params.items()}, {"_id": 0, "data": 1})
	if res is None: return None
	return json.loads(res["data"], object_hook=json_util.object_hook)
	