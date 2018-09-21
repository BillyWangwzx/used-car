#-*-coding:utf-8-*-
import urllib2
import re
import urlparse
import datetime
import time
import lxml.html
import csv
import sys
reload(sys)
sys.setdefaultencoding('utf8')
print sys.getdefaultencoding()
from selenium import webdriver

driver = webdriver.Firefox()


class Throttle:
    """Throttle downloading by sleeping between requests to same domain
    """

    def __init__(self, delay):
        # amount of delay between downloads for each domain
        self.delay = delay
        # timestamp of when a domain was last accessed
        self.domains = {}

    def wait(self, url):
        domain = urlparse.urlparse(url).netloc
        last_accessed = self.domains.get(domain)

        if self.delay > 0 and last_accessed is not None:
            sleep_secs = self.delay - (datetime.now() - last_accessed).seconds
            if sleep_secs > 0:
                time.sleep(sleep_secs)
        self.domains[domain] = datetime.now()


def download(url, proxy=None, num_retries=5):
    time.sleep(3)
    user_agent = {'User-Agent':'Mozilla/5.0(Macintosh; Intel Mac OS X 10_9_5) AppleWebKit 537.36(KHTML, like Grcko) Chrome',
                  'Accept':'text/html,application/xhtml+xml,application/xml; q=0/9,image/webp,*/*;q=0.8'
                               }
    print 'Downloading:', url
    headers = {'User-agent': user_agent}
    request = urllib2.Request(url, headers=headers)
    opener = urllib2.build_opener()
    if proxy:
        proxy_param = {urlparse.urlparse(url).scheme: proxy}
        opener.add_handler(urllib2.ProxyHandler(proxy_param))
    try:
        html = opener.open(request).read()
        print 'Download complete'
    except urllib2.URLError as e:
        print 'Download error:', e.reason
        html = None
        if num_retries > 0:
            if hasattr(e, 'code') and 500 <= e.code < 600:
                # recursively retry 2xx HTTP errors
                return download(url, num_retries=num_retries - 1)
    return html

def download2(url,num_retries = 5):
    try:
        driver.get(url)
        html = driver.page_source
        return html
    except:
        return download2(url, num_retries=num_retries-1)

def get_carlinks(url):
    '''return a list of house links from html'''
    html = download2(url)
    tree = lxml.html.fromstring(html)
    links = []
    links_elements = tree.cssselect('div.item_details> h3>a')
    for element in links_elements:
        links.append(element.attrib.get('href'))
    return links


class ScrapeCallback:
    def __init__(self):
        self.writer = csv.writer(open('C:\Users\wangzixi\Desktop\lianjia\\taoche_ty.csv', 'w'))
        self.field = ('总车型','价格','新车价','行驶时间','公里数','保养方式','使用类型','所在地','环境标准','年检到期日','保险到期日')
        print len(self.field)
        #self.field = [i.decode('utf8') for i in self.field]
        self.writer.writerow(self.field)

    def __call__(self, url):
        row = []
        print 'searching through', url
        html = download2(url)
        tree = lxml.html.fromstring(html)
        a1 = tree.cssselect('div.summary > div.summary-title > h1.title ')[0].text_content()
        row.append(a1)
        price = re.findall('([0-9]+\.[0-9]*)', tree.cssselect('div.summary-price-wrap > strong.price-this')[0].text_content())[0]
        row.append(price)
        #原厂价格
        price_new  = re.findall('([0-9]+\.[0-9]*)', tree.cssselect('div.summary-price-wrap > span.item')[0].text_content())[0]
        row.append(price_new)
        # 上牌时间 。。。。变速箱
        attri_elements = tree.cssselect('div.row > div.col-xs-6 > p ')
        for element in attri_elements:
            row.append(element.tail.strip())
        for i in range(len(row)):
            print self.field[i] + ':' + str(row[i])
        print len(row)
        self.writer.writerow(row)
        print 'successfully scraped'


scrape_callback = ScrapeCallback()

pages_url = []
for i in range(1, 51):
    pages_url.append('http://taiyuan.taoche.com/all/?page=%i#pagetag' % i)
seen_url = []
error_car = {}
for page_url in pages_url:
    houses_url = get_carlinks(page_url)
    for car_url in houses_url:
        if car_url not in seen_url:
            try:
                scrape_callback(car_url)
                seen_url.append(car_url)
                print len(seen_url), 'cars have been recorded'
            except IndexError:
                print 'outlierr!!!cannot catch', car_url
                error_car[car_url]=1


while error_car:
    cars_url = error_car.keys()
    for car_url in cars_url:
        try:
            scrape_callback(car_url)
            seen_url.append(car_url)
            print len(seen_url), 'cars have been recorded'
            error_car.pop(car_url, False)
        except IndexError:
            print 'outlierr!!!cannot catch', car_url
            error_car[car_url] += 1
    for car_url in error_car:
        if error_car[car_url] >= 5:
            error_car.pop(car_url, False)