from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from . import cache


def ticker_news_scraping(ticker) -> List[Dict]:
	page = requests.get(f"https://www.etnet.com.hk/www/eng/stocks/realtime/quote.php?code={'0' + ticker[:4]}", headers={
		'Referer': f'https://www.etnet.com.hk/www/eng/stocks/realtime/quote.php?code={"0" + ticker[:4]}',
		'Sec-Fetch-Site': 'same-origin'
	})
	soup = BeautifulSoup(page.content, "html.parser")
	rows = soup.find_all("div", attrs={"class": "DivArticleList"})

	out = []
	for row in rows:
		if row.find('span') is None: break
		out.append({
			'title': row.find('a').get_text(),
			'link': "https://www.etnet.com.hk/www/eng/stocks/realtime/" + row.find('a')['href'],
			'time': row.find('span').get_text()
		})
	
	return out


def scmp_scraping(limit=10, use_cache=True) -> List[Dict]:
	if use_cache:
		cache_res = cache.get_cached_result("scmp_scraping", {"limit": limit})
		if cache_res is not None:
			return cache_res

	page = requests.get("https://www.scmp.com/topics/hong-kong-stock-market")
	soup = BeautifulSoup(page.content, "html.parser")
	rows = list(soup.find_all("div", attrs={"class": "article-level"}))

	out = []
	for i in range(11, 12+limit):
		try:
			row = rows[i]
			title_tag = row.find('a')

			out.append({
				'title': title_tag.get_text().strip(),
				'link': 'https://www.scmp.com' + title_tag['href'],
				'time': row.find_all('span', attrs={'class': 'author__status-left-time'})[0].get_text()
			})
		except:
			continue
	
	cache.store_cached_result("scmp_scraping", {"limit": limit}, out)
	return out


def hkd_exchange_rate_scraping(use_cache=True) -> List[Dict]:
	if use_cache:
		cache_res = cache.get_cached_result("hkd_exchange_rate_scraping", {})
		if cache_res is not None:
			return cache_res

	page = requests.get("https://www.etnet.com.hk/www/eng/stocks/realtime/index.php")
	soup = BeautifulSoup(page.content, "html.parser")
	table = list(soup.find_all("div", attrs={"class": "DivLeftGridC2"}))[1]
	
	out = []
	even_rows = table.find_all("tr", attrs={"class": "evenRow"})
	odd_rows = table.find_all("tr", attrs={"class": "oddRow"})
	rows = even_rows + odd_rows
	for row in rows:
		content = row.find_all("td")
		if "HKD" in content[0].get_text(): # To avoid adding the USD exchange rates and other stuff
			out.append({
				"currency": content[0].get_text(),
				"buy": content[1].get_text(),
				"sell": content[2].get_text()
			})

	del out[-1] # Remove the dup. USD/HKD from the USD exchange rates table

	cache.store_cached_result("hkd_exchange_rate_scraping", {}, out)
	return out
	