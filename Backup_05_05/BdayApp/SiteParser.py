import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

SITE_LIST = {'amazon':'www.amazon.com'}

class URLParser():
    url = None
    def __init__(self, url):
        self.url = url

    def parse(self):
        dict_ = {}
        try:
            if "amazon" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                ids = soup.find_all(id="imgTagWrapperId")
                span_currency = soup.find(id="priceblock_ourprice")
                if span_currency is None:
                    span_currency = soup.find(id="priceblock_saleprice")
                str = span_currency.get_text()
                dict_['price'] = float(str.replace(',',''))
                for id in ids:
                    dict_['name'] = id.img['alt']
                    dict_['picture'] = id.img['data-old-hires']
                    dict_['website_name'] = 'amazon'
                    dict_['website_url'] = 'www.amazon.in'
                    if dict_['picture'] == "":
                        for key, value in eval(id.img['data-a-dynamic-image']).iteritems():
                            dict_['picture'] = key
                            logger.info(key)
                            break
                    return dict_
            elif "flipkart" in self.url:
                headers = {'Fk-Affiliate-Id':'affinfobd','Fk-Affiliate-Token':'f85cb358c9a04d99a623d845a0e21bd2'}
                api_url = 'https://affiliate-api.flipkart.net/affiliate/1.0/product.json?id='
                parsed_url = urlparse(url)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                id = parse_qs(parsed_url.query)['pid']
                response = requests.get(api_url+id[0],headers=headers)
                product_data = json.loads(response.content)
                dict_['name'] = product_data["productBaseInfoV1"]["title"]
                dict_['picture'] = product_data["productBaseInfoV1"]["imageUrls"]["400x400"]
                dict_['website_name'] = 'flipkart'
                dict_['website_url'] = 'www.flipkart.com'
                dict_['price'] = float(product_data["productBaseInfoV1"]["maximumRetailPrice"]["amount"])
                dict_['currency'] = product_data["productBaseInfoV1"]["maximumRetailPrice"]["currency"]
                self.url = product_data["productBaseInfoV1"]["productUrl"]
                return dict_
        except Exception as e:
            logger.error(e)
            return {}
