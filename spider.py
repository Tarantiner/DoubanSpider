import time
import json
import requests
from pyquery import PyQuery
import pymongo
from config import *
from proxy import ProxyHandler


class Spider:

    """
    登录豆瓣，爬取不同分类的rank信息，保存到数据库
    """
    db_action = {'txt': 'save_to_txt', 'mongo': 'save_to_mongo'}

    def __init__(self, type_name, type_id):
        """
        实例化，赋值一个proxyhandler属性
        :param type_name: 类型名，在数据存储时用到
        :param type_id: 类型id，再发送请求时用到
        """
        self.type_name = type_name
        self.type_id = type_id
        self.session = requests.session()
        self.proxyhandler = ProxyHandler('https')

    @property
    def param(self):
        """
        根据用户输入生成请求params
        :return:
        """
        return {
            'type': self.type_id, 'interval_id': '100:90',
            'action': '', 'start': '0', 'limit': MAX_COUNT,
        }

    def get_proxy(self):
        """
        获取代理
        """
        try:
            return next(self.proxyhandler.proxy_pool)
        except StopIteration:    # 代理用完了
            print('searching proxy...')
            time.sleep(CYCLE)
            self.proxyhandler.run()
            return self.get_proxy()

    def login(self, proxy):
        """
        登录
        成功：保存session和可用代理
        失败：重新获取代理并执行登录
        """
        try:
            self.session.post(url=LOGIN_URL, data=ACCOUNT, headers=HEADERS,
                              proxies=proxy, allow_redirects=False, timeout=3)
            valid_proxy = proxy
            print('valid proxy!')
            return valid_proxy
        except Exception as e:
            print('proxy invalid, trying new...')
            return self.login(self.get_proxy())

    @staticmethod
    def get_base_data(item):
        """
        获取ajax发送的json格式信息，处理成目标字典
        :param item: 未处理基本信息， dict形式
        :return:  处理完毕的基本信息，dict形式
        """
        base_data_dic = {
            '海报': item.get("cover_url"),
            '电影名称': item.get('title'),
            '演员': item.get('actors'),
            '类型': item.get('types'),
            '豆瓣评分': item.get('score')
        }
        return base_data_dic

    @staticmethod
    def query_filter(pq_obj, condition):
        """
        取字段值
        :param pq_obj: pyquery对象
        :param condition: '导演'
        :return: 'Stephen Chow'
        """
        return pq_obj('span.pl').filter(lambda i, this: PyQuery(this).text() == condition).next().text()

    def parse_more_info(self, html):
        """
        解析页面数据
        :param html: 每一条电影更多信息,未处理
        :return: {'导演', 'Stephen Chow',...}
        """
        conditions = ['导演', '编剧', '上映日期:', '片长:']
        doc = PyQuery(html)
        div = doc('#info')
        return {condition.replace(':', ''): self.query_filter(div, condition) for condition in conditions}

    @staticmethod
    def simple_parse(html):
        """
        推荐解析方式，更简单
        :param html: 每一条电影更多信息,未处理
        :return: 每一条电影更多信息,处理完毕
        """
        conditions = ['导演', '编剧', '上映日期', '语言', '片长']
        doc = PyQuery(html)
        div_text = doc('#info').text()
        info_lis = div_text.split('\n')
        dic = {info.split(':')[0].strip(): info.split(':')[1].strip().replace('/', ',') for info in info_lis}
        return {condition: dic.get(condition, '') for condition in conditions}

    def get_more_info(self, item):
        """
        详情页面获取更多信息
        :param item: 每一条电影信息,未处理
        :return: 每一条电影更多信息,处理完毕
        """
        more_into_text = self.session.get(url=item['url'], headers=HEADERS).text
        try:
            return self.parse_more_info(more_into_text)
        except Exception:  # 用pyquery方式解析
            return self.simple_parse(more_into_text)

    def process_item(self, item):
        """
        从ajax发的数据中拿到基本信息
        从ajax发的url中请求另一个页面，拿到更多信息
        :param item: 每一条电影信息,未处理
        :return: 每一条电影信息,已解析完毕
        """
        base_data = self.get_base_data(item)
        more_info = self.get_more_info(item)
        base_data.update(more_info)
        return base_data

    def get_movie_data(self, proxy):
        """
        获取电影信息
        :param proxy: 可用代理
        :return: 存储所有电影信息的生成器对象
        """
        res = self.session.get(url=BASE_URL, params=self.param,
                               headers=HEADERS, proxies=proxy, allow_redirects=False)
        if res.status_code == 200:
            json_items = json.loads(res.text)
            for item in json_items:
                yield self.process_item(item)

    def save_to_mongo(self, movie_datas):
        """
        存到数据库
        :param movie_datas: 所有电影信息，generator
        """
        client = pymongo.MongoClient(MONGO_URL)
        db = client[MONGO_DB]
        for movie_data in movie_datas:
            db[self.type_name].insert(movie_data)

    def save_to_txt(self, movie_datas):
        """
        存到txt文件
        :param movie_datas: 所有电影信息，generator
        """
        file_name = self.type_name + '.txt'
        with open(f'./db/{file_name}', 'w', encoding='utf-8') as fb:
            fb.write(f'{self.type_name}:抓取到{MAX_COUNT}条{self.type_name}电影：\n')
            fb.write('#' * 100 + '\n')
            for movie_data in movie_datas:
                for key, value in movie_data.items():
                    fb.write(f'{key}: {value}\n')
                fb.write('-' * 100 + '\n')

    def run(self):
        """
        总调度
        1.获取代理
        2.用户登录
        3.爬取数据
        4.持久化存储
        """
        self.proxyhandler.run()
        proxy = self.get_proxy()
        valid_proxy = self.login(proxy)
        movie_datas = self.get_movie_data(valid_proxy)
        getattr(self, self.db_action[DB])(movie_datas)


def get_type():
    """
    拿到爬取网站必要的type_id
    """
    type_dict = {}
    import re
    res = requests.get('https://movie.douban.com/chart', headers=HEADERS)
    type_lis = re.findall('<a href="/typerank\?type_name=(.*?)&type=(.*?)&.*?">', res.text)
    for item in type_lis:
        type_dict[item[0]] = item[1]
    return type_dict


def main():
    """
    入口函数,根据用户输入类型crawl
    """
    type_dict = get_type()
    while True:
        print(' '.join(list(type_dict.keys())))
        type_name = input('choose type to crawl(press "q" to exit)>>>').strip()
        if type_name != 'q':
            if type_name in type_dict:
                type_id = type_dict[type_name]
                spider = Spider(type_name, type_id)
                spider.run()
            else:
                continue
        else:
            exit('exit crawling, bye!')


if __name__ == '__main__':
    main()
