from typing import Dict, List

import requests
from bs4 import BeautifulSoup


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


def scmp_scraping(limit=10) -> List[Dict]:
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

	return out
