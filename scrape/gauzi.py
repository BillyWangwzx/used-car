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
    time.sleep(5)
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
        time.sleep(5)
        html = driver.page_source
        return html
    except:
        return download2(url, num_retries=num_retries-1)

def get_carlinks(url):
    '''return a list of house links from html'''
    html = download2(url)
    tree = lxml.html.fromstring(html)
    links = []
    links_elements = tree.cssselect('a.car-a')
    for element in links_elements:
        links.append('http://www.guazi.com'+element.attrib.get('href'))
    return links


class ScrapeCallback:
    def __init__(self):
        self.writer = csv.writer(open('C:\Users\wangzixi\Desktop\lianjia\\guazi_qd.csv', 'w'))
        self.field = ('总车型','车型1','款式年份','卖家报价(万)','新车指导价(万)','上牌时间','公里数','上牌城市','排放标准','变速箱1','服务费',
                      '厂商','级别','发动机','变速箱详情','车身结构','长宽高','轴承','行李容积','整备质量','排量',
                      '进气形式','气缸','最大马力','最大扭矩','燃料类型','燃油标号','供油方式','排放标准','驱动方式','助力类型'
                      ,'前悬挂类型','后悬挂类型','前制动类型','后制动类型','驻车制动类型','前轮胎规格','后轮胎规格','主副驾驶安全气囊',
                      '前后排侧气囊','前后排头部气囊','胎压检测','车内中控锁','儿童座椅接口','无钥匙启动系统','防抱死系统',
                      '车身稳定控制','电动天窗','全景天窗','电动吸合门','感应后备箱','感应雨刷','前后电动车窗','后视镜电动调节',
                      '后视镜电动调节','后视镜加热','多功能方向盘','定速巡航','空调','自动空调','GPS导航','倒车雷达','倒车影像系统',
                      '真皮座椅','前后排座椅加热','事故排查','泡水排查','火烧排查','机舱项','底盘悬架项','安全系统','外部配置'
                      ,'内部配置','灯光系统','高科技配置','随车工具','仪表台指示灯','发动机状态','变速箱及转向'
                      ,'缺陷项检测','漆面修复检测','钣金修复检测','外观件更换检测')
        print len(self.field)
        #self.field = [i.decode('utf8') for i in self.field]
        self.writer.writerow(self.field)

    def __call__(self, url):
        row = []
        print 'searching through', url
        html = download2(url)
        tree = lxml.html.fromstring(html)
        a1 = tree.cssselect('div.product-textbox > div.titlebox > p')[0].text_content()
        row.append(a1)
        row.append(a1.split(' ')[0])
        row.append(a1.split(' ')[1])
        price = re.findall('([0-9]+\.[0-9]*)',tree.cssselect('div.product-textbox > div.pricebox > span.pricestype')[0].text_content())[0]
        row.append(price)
        #原厂价格
        price_new  = re.findall('([0-9]+\.[0-9]*)',tree.cssselect('div.pricebox > span.newcarprice')[0].text_content())[0]
        row.append(price_new)
        # 上牌时间 。。。。变速箱
        attri_elements = tree.cssselect('div.product-textbox > ul.assort > li > span')
        for element in attri_elements:
            row.append(element.text_content().split()[0].strip())
        #服务费
        row.append(tree.cssselect('div.service-protect > div.car-fuwu > span')[0].text_content())
        attri_elements = tree.cssselect('table.param-table > tbody > tr > td.td2')
        for element in attri_elements:
            row.append(element.text_content().strip())
        #专业检测
        attri_elements = tree.cssselect('ul.jiance-con > li > div.c-list')
        for element in attri_elements:
            if element.cssselect('i.icon-right'):
                row.append(0)
            else:
                row.append(re.findall('[0-9]+',element.cssselect('i.icon-yellow-error > span.fc-org-text')[0].text_content())[0])
        for i in range(len(row)):
            print self.field[i] + ':' + str(row[i])
        print len(row)
        self.writer.writerow(row)
        print 'successfully scraped'


scrape_callback = ScrapeCallback()

pages_url = []
for i in range(1, 59):
    pages_url.append('https://www.guazi.com/qd/buy/o%d/#bread' % i)
seen_url = []
error_car = {}
while pages_url:
    page_url = pages_url.pop()
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