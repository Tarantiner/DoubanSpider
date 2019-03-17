CYCLE = 20    # 代理使用完后重新抓取等待时长
MAX_COUNT = '5'    # 抓取个数
DB = 'txt'    # 存储方式，可选txt or mongo
MONGO_URL = 'localhost'    # 本地库/远程库
MONGO_DB = 'douban'    # mongodb数据库名
PROXY_URL = 'https://www.xicidaili.com/'    # 抓取的公共代理的网址
LOGIN_URL = 'https://accounts.douban.com/j/mobile/login/basic'    # 豆瓣登录地址
BASE_URL = 'https://movie.douban.com/j/chart/top_list?'    # 豆瓣电影网


######################################
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'
}

######################################
ACCOUNT = {
    'ck': '',
    'name': 'YOUR ACCOUNT',
    'password': 'YOUR PASSWORD',
    'remember': 'false',
    'ticket': ''
}
