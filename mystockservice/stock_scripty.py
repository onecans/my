import scrapy


class QuotesSpider(scrapy.Spider):
    name = "quotes"

    def start_requests(self):
        urls = [
            'http://query.sse.com.cn/security/stock/queryEquityChangeAndReason.do?jsonCallBack=jsonpCallback82202&isPagination=true&companyCode=600000&pageHelp.pageSize=25&pageHelp.pageCount=50&pageHelp.pageNo=1&pageHelp.beginPage=1&pageHelp.cacheSize=1&pageHelp.endPage=5&_=1537680710408',
            'http://query.sse.com.cn/security/stock/queryEquityChangeAndReason.do?jsonCallBack=jsonpCallback82202&isPagination=true&companyCode=601600&pageHelp.pageSize=25&pageHelp.pageCount=50&pageHelp.pageNo=1&pageHelp.beginPage=1&pageHelp.cacheSize=1&pageHelp.endPage=5&_=1537680710408',
        ]
        headers = {'Pragma': 'no-cache', 'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                   'Connection': 'keep-alive', 'Cache-Control': 'no-cache',
                   'Accept': '*/*', 'Referer': 'http://www.sse.com.cn/assortment/stock/list/info/capital/index.shtml',
                   'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.92 Safari/537.36'}
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse, headers=headers)

    def parse(self, response):
        page = response.url.split("/")[-2]
        filename = 'quotes-%s.html' % page
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)
