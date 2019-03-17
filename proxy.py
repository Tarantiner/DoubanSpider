from pyquery import PyQuery as pq
from config import *


class ProxyHandler:
    proxy_pool = None

    def __init__(self, protocol):
        self.protocol = protocol

    @staticmethod
    def crawl_proxy_url():
        """
        :param url: 要爬取的公共代理网站
        :return: 未解析的爬取数据,pyquery对象
        """
        doc = pq(url=PROXY_URL, headers=HEADERS)
        return doc

    def parse_html(self, doc):
        """
        对爬取到的内容解析
        :param doc: 未解析的爬取数据,pyquery对象
        :return: 爬取所有代理的生成器对象
        """
        proxy_text_trs = doc('#ip_list tr').filter(lambda i, this: i > 1).items()
        for tr in proxy_text_trs:
            protocol = tr('td').eq(5).text().lower()
            if protocol == self.protocol:
                ip = tr('td').eq(1).text()
                port = tr('td').eq(2).text()
                yield {protocol: '%s://%s:%s'.lower() % (protocol, ip, port)}

    def run(self):
        doc = self.crawl_proxy_url()
        self.proxy_pool = self.parse_html(doc)




