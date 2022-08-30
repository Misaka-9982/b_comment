import random
import requests
import json
import time


class BilibiliCommentSpider:
    def __init__(self, oid=32036576, pagenum=1):
        self.oid = oid  # 视频av号
        self.pagenum = pagenum  # 爬取总页数
        self.url = 'https://api.bilibili.com/x/v2/reply/main?'
        self.headers = {'UserAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                     'Chrome/104.0.5112.102 Safari/537.36 Edg/104.0.1293.63'}
        self.next = 0  # 评论页数第一页是0，第二页是2，随后顺延
        self.querystrparams = f'jsonp=jsonp&next={self.next}&type=1&oid={self.oid}&mode=3&plat=1'
        self.allpagedict = []

    def request_json_dict(self):
        t1 = time.time()
        print(f'开始爬取评论   {time.asctime()}')
        for i in range(self.pagenum):
            t2 = time.time()
            print(f'正在爬取{i+1}/{self.pagenum}页，已用时{t2-t1:.2f}秒')
            res = requests.get(self.url, params=self.querystrparams, headers=self.headers)
            commentdict = json.loads(res.text)
            self.allpagedict.append(commentdict)
            # b站api规则，第一页从0开始，第二页next=2，跳过1
            self.next += 1 if self.next != 0 else 2  # 该语法else后针对if前的值，不是整个表达式
            self.querystrparams = f'jsonp=jsonp&next={self.next}&type=1&oid={self.oid}&mode=3&plat=1'
            time.sleep(random.uniform(1, 3))   # 随机间隔时间范围
        t2 = time.time()
        print(f'爬取结束，用时{t2-t1:.2f}秒    {time.asctime()}')
        return self.allpagedict

    def getpages(self, n):  # 从0开始   # 一页20个主评论
        if n > self.pagenum:
            raise IndexError(f'第{n}页未抓取！')
        else:
            return self.allpagedict[n]

    def users_level_ratio(self):
        levellist = [0]*8   # 对应0-6闪电 八个等级
        for i in range(self.pagenum):
            page: dict = self.getpages(i)  # 不加dict类型注解时，下一行编译器会有索引类型警告
            mainreplynums = len(page['data']['replies'])  # 每页多少条主回复
            # 统计主回复
            for x in range(mainreplynums):
                if page['data']['replies'][x]['member']['is_senior_member'] == 1:
                    levellist[7] += 1
                else:
                    levellist[page['data']['replies'][x]['member']['level_info']['current_level']] += 1
                # 统计子回复
                subreplynums = len(page['data']['replies']['replies'])  # 每条主回复多少条子回复
                for y in range(subreplynums):
                    if page['data']['replies']['replies'][y]['member']['is_senior_member'] == 1:
                        levellist[7] += 1
                    else:
                        levellist[page['data']['replies']['replies'][y]['member']['level_info']['current_level']] += 1

    def run(self):
        allpagedict = self.request_json_dict()
        self.users_level_ratio()


if __name__ == '__main__':
    spider = BilibiliCommentSpider()
    spider.run()
