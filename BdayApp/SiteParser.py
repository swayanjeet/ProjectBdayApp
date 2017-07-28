import requests
from bs4 import BeautifulSoup
from urlparse import urlparse, parse_qs
import json
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
        dict_['url'] = self.url
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
            elif "infibeam" in self.url:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response= requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                dict_['website_name'] = 'infibeam'
                dict_['website_url'] = 'www.infibeam.com'
                dict_['name'] = soup.find(id="title").h1.get_text()
                dict_['picture'] = soup.find(id="product-images").find("img",class_='img-responsive')['content']
                discounted_price = soup.find(id='price-after-discount').span.next_sibling
                if discounted_price is not None:
                    dict_['price'] = float(discounted_price.get_text().replace(',',''))
                else:
                    base_price = soup.find(id='base-price').span.next_sibling.get_text()
                    dict_['price'] = float(base_price.get_text().replace(',',''))
                if '?' in self.url:
                    dict_['url'] = self.url+'&trackId=affinfobd'
                else:
                    dict_['url'] = self.url+'?trackId=affinfobd'
                return dict_
            elif "flipkart" in self.url:
                headers = {'Fk-Affiliate-Id':'affinfobd','Fk-Affiliate-Token':'f85cb358c9a04d99a623d845a0e21bd2'}
                api_url = 'https://affiliate-api.flipkart.net/affiliate/1.0/product.json?id='
                parsed_url = urlparse(self.url)
                id = parse_qs(parsed_url.query)['pid']
                response = requests.get(api_url+id[0],headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                product_data = json.loads(response.content)
                dict_['name'] = product_data["productBaseInfoV1"]["title"]
                dict_['picture'] = product_data["productBaseInfoV1"]["imageUrls"]["400x400"]
                dict_['website_name'] = 'flipkart'
                dict_['website_url'] = 'www.flipkart.com'
                if "flipkartSpecialPrice" in product_data["productBaseInfoV1"]:
                    dict_['price'] = float(product_data["productBaseInfoV1"]["flipkartSpecialPrice"]["amount"])
                    dict_['currency'] = product_data["productBaseInfoV1"]["flipkartSpecialPrice"]["currency"]
                else:    
                    dict_['price'] = float(product_data["productBaseInfoV1"]["flipkartSellingPrice"]["amount"])
                    dict_['currency'] = product_data["productBaseInfoV1"]["flipkartSellingPrice"]["currency"]
                dict_['url'] = product_data["productBaseInfoV1"]["productUrl"]
                return dict_
            elif "koovs" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(class_="product-name").find("h1").find("span").get_text()
                if "KOOVS" in title:
                    title = title[6:]
                dict_['name'] = title
                image = soup.find(id="mainProductImage").find("img", id="finalimage")
                dict_['picture'] = image['src']
                price = soup.find(class_='product-price').span.next_sibling.get_text()
                dict_['price'] = float(price.replace(',',''))
                dict_['website_name'] = 'koovs'
                dict_['website_url'] = 'www.koovs.com'
                dict_['url'] = self.url
                return dict_
            elif "zivame" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                meta_data = soup.find(id="product-meta-data")
                dict_['name'] = meta_data['data-productname']
                dict_['picture'] = meta_data['data-cdn-url']+meta_data['data-productimg']
                price = meta_data['data-newprice']
                dict_['price'] = float(price.replace('Rs.',''))
                dict_['website_name'] = 'zivame'
                dict_['website_url'] = 'www.zivame.com'
                dict_['url'] = self.url
                return dict_
            elif "nykaa" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(class_="product-name").get_text()
                dict_['name'] = title.rstrip()
                image = soup.find(class_="product-image-box-container").find(class_="product-image-box").find(class_="product-image product-image-zoom").img
                dict_['picture'] = image['src']
                price_span = soup.find(class_='regular-price desk-regular-price')
                if price_span is None:
                    price_span = soup.find(class_='special-price desk-special-price')
                price = price_span.span.get_text()
                dict_['price'] = float(price.replace('Rs.',''))
                dict_['website_name'] = 'nykaa'
                dict_['website_url'] = 'www.nykaa.com'
                dict_['url'] = self.url
                return dict_
            elif "clovia" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(class_="product-title top-stars").get_text()
                dict_['name'] = title.rstrip().lstrip()
                image = soup.find(class_="row transitionfx").find(class_="productImageZoom").find(class_="zoom om lazy").img
                dict_['picture'] = image['src']
                price = soup.find(class_="price-sales").span.meta['content']
                price = price.lstrip().rstrip()
                dict_['price'] = float(price)
                dict_['website_name'] = 'clovia'
                dict_['website_url'] = 'www.clovia.com'
                dict_['url'] = self.url
                return dict_
            elif "coolwinks" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(class_="short-description").get_text()
                dict_['name'] = title.rstrip().lstrip()
                image = soup.find(class_="ldetails").find(class_="container").find(class_="row").find(class_="col-md-6 col-sm-12").ul.li.img
                dict_['picture'] = image['src']
                price = soup.find(class_="regular_price").get_text()
                price = price.lstrip().rstrip()
                dict_['price'] = float(price.replace('Rs.',''))
                dict_['website_name'] = 'coolwinks'
                dict_['website_url'] = 'www.coolwinks.com'
                dict_['url'] = self.url
                return dict_
            elif "ajio" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')    
                title = soup.find(class_="fnl-pdp-title").get_text().rstrip().lstrip()+" "+soup.find(class_="fnl-pdp-subtitle").get_text().rstrip().lstrip()
                dict_['name'] = title
                image = soup.find(id="primary_image").img
                dict_['picture'] = 'https://www.ajio.com'+image['src']
                price = soup.find(id="finprc-amt").get_text()
                price = price.lstrip().rstrip()
                dict_['price'] = float(price.replace('Rs.',''))
                dict_['website_name'] = 'ajio'
                dict_['website_url'] = 'www.ajio.com'
                dict_['url'] = self.url
                return dict_
            elif "abof" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(class_="product-detail__title").get_text()
                dict_['name'] = title.rstrip().lstrip()
                image = soup.find(class_="image-magnifier-component").img
                dict_['picture'] = image['src']
                price = soup.find(class_="prices__price prices__price--selling")
                dict_['price'] = float(price['content'])
                dict_['website_name'] = 'abof'
                dict_['website_url'] = 'www.abof.com'
                dict_['url'] = self.url
                return dict_
            elif "fabfurnish" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(id="product_name")
                dict_['name'] = title['product_name']
                image = soup.find(id="gallery").find(id="imgThumb_1").find('a')['href']
                dict_['picture'] = image
                price = soup.find(class_="final_price_pdp mbs").find(id="final_price_text").get_text()
                price = price.rstrip().lstrip()
                dict_['price'] = float(price.replace(',',''))
                dict_['website_name'] = 'fabfurnish'
                dict_['website_url'] = 'www.fabfurnish.com'
                dict_['url'] = self.url
                return dict_
            elif "fnp" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(class_="item-heading")
                dict_['name'] = title['title']
                image = soup.find(id="detailImage1")
                dict_['picture'] = image['src']
                meta_list = soup.find(class_="pricediv").find_all("meta")
                price = None
                for meta in meta_list:
                    if meta['itemprop'] == "price":
                        price = meta['content']
                dict_['price'] = float(price)
                dict_['website_name'] = 'fnp'
                dict_['website_url'] = 'www.fnp.com'
                dict_['url'] = self.url
                return dict_
            elif "footprint360" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(class_="col-lg-5 col-md-7 col-sm-12 col-xs-12 product-shop product-view").h1.span.get_text()
                dict_['name'] = title
                image = soup.find(id="image")
                dict_['picture'] = image['src']
                price = soup.find(class_="regular-price")
                if price is None:
                    price = soup.find(class_="special-price").find(class_="price").get_text()
                else:
                    price = price.span.get_text()
                price = price.lstrip().rstrip()
                price = price[1:]
                dict_['price'] = float(price.replace(',',''))
                dict_['website_name'] = 'footprint360'
                dict_['website_url'] = 'www.footprint360.com'
                dict_['url'] = self.url
                return dict_
            elif "giftalove" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(id="ctl00_ContentPlaceHolder1_Product1_lblProductname").h1.get_text()
                dict_['name'] = title
                image = soup.find(id="ctl00_ContentPlaceHolder1_Product1_Imagedetail").img
                dict_['picture'] = image['src']
                price = soup.find(class_="price inr").get_text()
                dict_['price'] = float(price.replace('Rs.',''))
                dict_['website_name'] = 'giftalove'
                dict_['website_url'] = 'www.giftalove.com'
                dict_['url'] = self.url
                return dict_
            elif "giftease" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(class_="product-name resGT801").h1.get_text()
                dict_['name'] = title
                image = soup.find(id="zoom1")['href']
                dict_['picture'] = image
                price = soup.find(class_="priceRed").find(class_="price").get_text()
                dict_['price'] = float(price.replace('Rs.','').replace(',',''))
                dict_['website_name'] = 'giftease'
                dict_['website_url'] = 'www.giftease.com'
                dict_['url'] = self.url
                return dict_
            elif "igp" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(class_="pdp-product-name").get_text().rstrip().lstrip()
                dict_['name'] = title
                image = soup.find(class_="intrinsic intrinsic-square").img
                dict_['picture'] = image['src']
                price = soup.find(class_="product-price-container").span.get_text()
                dict_['price'] = float(price.replace('Rs.','').replace(',',''))
                dict_['website_name'] = 'igp'
                dict_['website_url'] = 'www.igp.com'
                dict_['url'] = self.url
                return dict_
            elif "lenskart" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(class_="prcdt-overview").find(class_="title").h1.get_text().rstrip().lstrip().replace('\n',' ')
                dict_['name'] = title
                image = soup.find(id="zoom")['href']
                dict_['picture'] = image
                price = soup.find(class_="lenskart").find(class_="price").meta['content'].rstrip().lstrip()
                dict_['price'] = float(price.replace('Rs.','').replace(',',''))
                dict_['website_name'] = 'lenskart'
                dict_['website_url'] = 'www.lenskart.com'
                dict_['url'] = self.url
                return dict_
            elif "organicindiashop" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(class_="prodct-name").h1.span.get_text()
                dict_['name'] = title
                image = 'https://www.organicindiashop.com/'+soup.find(id="MagicZoomPlusImage4816")['href']
                dict_['picture'] = image
                price = soup.find(class_="price").b.get_text().lstrip().rstrip()
                dict_['price'] = float(price.replace('Rs.','').replace(',',''))
                dict_['website_name'] = 'organicindiashop'
                dict_['website_url'] = 'www.organicindiashop.com'
                dict_['url'] = self.url
                return dict_
            elif "raymondnext" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(class_="product-title").h2.get_text().lstrip().rstrip()
                dict_['name'] = title
                image = soup.find(class_="product-photo-container hidden-xs").a['href']
                dict_['picture'] = image
                price = soup.find(class_="prices").get_text().lstrip().rstrip()
                dict_['price'] = float(price.replace('Rs.','').replace(',',''))
                dict_['website_name'] = 'raymondnext'
                dict_['website_url'] = 'www.raymondnext.com'
                dict_['url'] = self.url
                return dict_
            elif "thebodyshop" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(class_="ctl_aboutbrand").h1.get_text().lstrip().rstrip()
                dict_['name'] = title
                image = soup.find(id="zoomImg").img['src']
                dict_['picture'] = image
                price = soup.find(class_="sp_amt").get_text().lstrip().rstrip()
                dict_['price'] = float(price.replace('Rs.','').replace(',',''))
                dict_['website_name'] = 'thebodyshop'
                dict_['website_url'] = 'www.thebodyshop.com'
                dict_['url'] = self.url
                return dict_
            elif "thepostbox" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(class_="section-title desktop-12 mobile-3").h1.get_text().lstrip().rstrip()
                dict_['name'] = title
                image = soup.find(class_="desktop-10 main-product-image").img['src']
                dict_['picture'] = image
                price = soup.find(class_="product-price").get_text().lstrip().rstrip()
                dict_['price'] = float(price.replace('Rs.','').replace(',',''))
                dict_['website_name'] = 'thepostbox'
                dict_['website_url'] = 'www.thepostbox.com'
                dict_['url'] = self.url
                return dict_
            elif "udemy" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(class_="clp-lead__title").get_text().lstrip().rstrip()
                dict_['name'] = title
                image = soup.find(class_="introduction-asset__img")['src']
                dict_['picture'] = image
                price = soup.find(class_="price-text__current").get_text().lstrip().rstrip()
                price = price[price.index("$")+1:]
                conversion_rate = 64.66
                dict_['price'] = float(price.replace('Rs.','').replace(',',''))*conversion_rate
                dict_['website_name'] = 'udemy'
                dict_['website_url'] = 'www.udemy.com'
                dict_['url'] = self.url
                return dict_
            elif "flaberry" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                form = soup.find(id="cart_form")['action']
                form = form[:len(form)-1]
                product_id = form[form.rfind('/')+1:]
                api_url = 'https://www.flaberry.com/ajax/1.php'
                payload = {'product_id': product_id}
                response = requests.post(api_url,payload)
                if response.status_code is not 200:
                    return dict_
                json_obj = json.loads(response.text)
                title = soup.find(class_="col-md-12 col-xs-12 product-description-box").find(class_="col-md-12 remove_left_padding").label.get_text()
                dict_['name'] = title
                image = json_obj['image_url']
                dict_['picture'] = image
                price = json_obj['original_price']
                dict_['price'] = float(price.replace('Rs.','').replace(',',''))
                dict_['website_name'] = 'flaberry'
                dict_['website_url'] = 'www.flaberry.com'
                dict_['url'] = self.url
                return dict_
            elif "henryandsmith" in self.url:
                #self.url = 'http://www.amazon.in/GM-Indicator-Shutter-International-Sockets/dp/B008XT42JU/ref=lp_1388888031_1_1?s=electronics&ie=UTF8&qid=1481980042&sr=1-1'
                #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                response = requests.get(self.url, headers=headers)
                dict_['status_code'] = response.status_code
                if response.status_code is not 200:
                    return dict_
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find(class_="product-title entry-title").get_text().rstrip().lstrip()
                dict_['name'] = title
                image = soup.find(class_="woocommerce-main-image zoom")['href']
                dict_['picture'] = image
                price = soup.find(class_="price-wrapper").meta['content']
                dict_['price'] = float(price)
                dict_['website_name'] = 'henryandsmith'
                dict_['website_url'] = 'www.henryandsmith.com'
                dict_['url'] = self.url
                return dict_
        except Exception as e:
            logger.error(e)
            return {}