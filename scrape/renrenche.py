#-*-coding:utf-8-*-
import urllib2
import re
import urlparse
import datetime
import time
import lxml.html
import csv
import sys
import random
reload(sys)
sys.setdefaultencoding('utf8')
print sys.getdefaultencoding()


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


def download(url, user_agent='hello', proxy=None, num_retries=5):
    #time.sleep(5)
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



def get_carlinks(url):
    '''return a list of house links from html'''
    html = download(url)
    tree = lxml.html.fromstring(html)
    links = []
    links_elements = tree.cssselect('div.jscroll-added > div.container > ul.row-fluid > li.span6 > a')
    for element in links_elements:
        links.append('http://www.renrenche.com'+element.attrib.get('href'))
    return links


class ScrapeCallback:
    def __init__(self):
        self.writer = csv.writer(open('C:\Users\wangzixi\Desktop\lianjia\\renrenche1.csv', 'w'))
        self.field = ('总车型','卖家报价','上牌时间','公里数','排放标准','排量','上牌城市','服务费',
                      '车型','厂商新车指导价','厂商','发动机','变速箱')
        #self.field = [i.decode('utf8') for i in self.field]
        self.writer.writerow(self.field)

    def __call__(self, url):
        row = []
        print 'searching through', url
        html = download(url)
        tree = lxml.html.fromstring(html)
        a1 = tree.cssselect('div.version3-detail-header-right > div.right-container > div.title > h1.title-name')[0].text_content()
        row.append(a1)
        price = tree.cssselect('p.price')[0].text_content()
        row.append(price)
        attri_elements = tree.cssselect('ul.row-fluid > li > div > p > strong')
        for element in attri_elements:
            row.append(element.text_content().strip())
        attri_elements = tree.cssselect('ul.row-fluid > li > div > strong')
        for element in attri_elements:
            row.append(element.text_content().strip())
        row.append(tree.cssselect('p.detail-title-right-tagP > strong')[0].text_content())
        row.append(tree.cssselect('div.item-value')[0].text_content().strip())
        attri_elements = tree.cssselect('tr > td > div.item-value')
        for i in range(5):
            row.append(attri_elements[i].text_content().strip())
        print row
        for i in row:
            print i.encode('utf8')
        self.writer.writerow(row)
        print 'successfully scraped'


scrape_callback = ScrapeCallback()

pages_url = []
for i in range(1, 51):
    pages_url.append('https://www.renrenche.com/bj/ershouche/p%d/' % i)
seen_url = []
error_house = []
while pages_url:
    page_url = pages_url.pop()
    houses_url = get_carlinks(page_url)
    for house_url in houses_url:
        if house_url not in seen_url:
            try:
                scrape_callback(house_url)
                seen_url.append(house_url)
                print len(seen_url), 'houses have been recorded'
            except IndexError:
                print 'outlierr!!!cannot catch', house_url
                error_house.append(house_url)
                # except TypeError:
                # print 'please wait', timer.delay, 'seconds'
                # timer.wait()
                # book_html = download(book_url, user_agent = 'wtf')
                # scrape_callback(book_url,book_html)

