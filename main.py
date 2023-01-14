import os.path
import random
import requests
import json
import time
import jieba
import re
import csv

import bv_av


class BilibiliCommentSpider:
    def __init__(self, vid: str, pagenum=1, delay=3, mode=3):
        if vid.isnumeric():       # 纯数字av号
            self.oid = int(vid)
        else:                    # BV开头的bv号
            self.oid = bv_av.dec(vid)
        # self.delay = delay   # 爬取延迟随机范围
        self.mode = mode     # mode=3按热门，mode=2按时间
        self.pagenum = pagenum  # 爬取总页数
        self.url = 'https://api.bilibili.com/x/v2/reply/main?'
        self.headers = {'UserAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                     'Chrome/104.0.5112.102 Safari/537.36 Edg/104.0.1293.63'}
        self.next = 0  # 评论页数第一页是0，第二页是2，随后顺延
        self.querystrparams = f'jsonp=jsonp&next={self.next}&type=1&oid={self.oid}&mode={self.mode}&plat=1'
        self.allpagedict = []   # 所有页的集合
        self.sortedcomment = []   # 主回复和子回复整理后分开存储
        self.vidname = None

    def get_basic_info(self):  # 获取标题等
        url = f'https://www.bilibili.com/video/av{self.oid}'
        res = requests.get(url, headers=self.headers)
        title = re.findall('<title data-vue-meta="true">(.*?)</title>', res.text)
        if len(title) == 0:
            title = re.findall('<html>.*?<title>(.*?)</title>', res.text)
        try:
            return title[0]
        except IndexError:
            return '[ERROR]未解析到视频名称'

    def request_json_dict(self):
        t1 = time.time()
        print(f'开始爬取评论   {time.asctime()}')
        for i in range(self.pagenum):
            t2 = time.time()
            print(f'正在爬取{i + 1}/{self.pagenum}页，已用时{t2 - t1:.2f}秒')
            try:
                res = requests.get(self.url, params=self.querystrparams, headers=self.headers)
            except (requests.exceptions.SSLError, requests.exceptions.ProxyError):
                exit('SSL/代理错误，请关闭代理或检查网络设置')
            except Exception as e:
                exit(f'未知错误！\n{repr(e)}')
            commentdict = json.loads(res.text)
            self.allpagedict.append(commentdict)
            # b站api规则，第一页从0开始，第二页next=2，跳过1
            self.next += 1 if self.next != 0 else 2  # 该语法else后针对if前的值，不是整个表达式
            self.querystrparams = f'jsonp=jsonp&next={self.next}&type=1&oid={self.oid}&mode=3&plat=1'
            time.sleep(random.uniform(1, 3))  # 随机间隔时间范围
        t2 = time.time()
        print(f'爬取结束，用时{t2 - t1:.2f}秒    {time.asctime()}')
        print('开始整合评论')
        self.sortcomment()
        return self.allpagedict

    def getpages(self, n) -> dict:  # 从0开始   # 一页20个主评论
        if n > self.pagenum:
            raise IndexError(f'第{n}页未抓取！')
        else:
            return self.allpagedict[n]

    # def getpagereplynums(self, page: dict):   # 统计传入页内容字典中，所有

    def users_level_ratio(self):
        levellist = [0] * 8  # 对应0-6闪电 八个等级
        for comment in self.sortedcomment:
            if comment['member']['is_senior_member'] == 1:
                levellist[7] += 1
            else:
                levellist[comment['member']['level_info']['current_level']] += 1

        print(
            f'level 0: {levellist[0]}\nlevel 1: {levellist[1]}\nlevel 2: {levellist[2]}\nlevel 3: {levellist[3]}\nlevel 4: '
            f'{levellist[4]}\nlevel 5: {levellist[5]}\nlevel 6: {levellist[6]}\nlevel 6+: {levellist[7]}\n'
            f'视频名称: {self.vidname}   AV{self.oid}\n  共计{sum(levellist)}条评论')
        print('爬取逻辑按热度排序') if self.mode == 3 else print('爬取逻辑按时间倒序')
        print(
            f'  0-4级占比{(sum(levellist[0:5]) / sum(levellist)) * 100:.2f}%   '
            f'5级及以上占比{(sum(levellist[5:]) / sum(levellist)) * 100:.2f}%   6级及以上占比{(sum(levellist[6:]) / sum(levellist)) * 100:.2f}%'
            f'   6+级占比{(levellist[7] / sum(levellist)) * 100:.2f}%')

    def words_frequency(self):
        commentlist = []
        for i in range(self.pagenum):
            page: dict = self.getpages(i)  # 不加dict类型注解时，下一行编译器会有索引类型警告

    def sortcomment(self):   # 将主次回复同等级整合
        for num in range(pagenum):
            page = self.getpages(num)
            if page.get('data').get('replies') is not None:   # 防止无回复时产生keyerror
                for mainreply in page['data']['replies']:  # 主回复
                    if mainreply.get('replies') is not None:
                        for subreply in mainreply['replies']:  # 子回复
                            self.sortedcomment.append(subreply)

                        del mainreply['replies']
                        self.sortedcomment.append(mainreply)

            else:
                print(f'第{num}页无评论！')

    def save_as_csv(self):
        save = input('保存所有评论为csv格式输入y，否则n')
        if save == 'y':
            verbose = input('选择内容详细程度（默认2，回车默认）:\n1、用户名+内容\n2、uid+用户名+性别+等级+时间+内容\n3、（暂未开发）\n')
            if verbose == '':
                verbose = 2
            elif verbose.isnumeric():
                verbose = int(verbose)

            n = 1  # 同名文件编号
            while os.path.isfile(f'{self.vidname}-{n}'):
                n += 1
            # newline=''防止换行符转换错误
            with open(f'{self.vidname}-{n}.csv', 'w', newline='', encoding='utf_8_sig') as f:  # utf-8 BOM 否则excel无法识别
                writer = csv.writer(f)
                if verbose == 1:
                    writer.writerow(['用户名', '内容'])  # 表头
                    for comment in self.sortedcomment:
                        writer.writerow([comment['member']['uname'], comment['content']['message']])
                    print(f'已保存到{self.vidname}-{n}.csv')
                elif verbose == 2:
                    writer.writerow(['uid', '用户名', '性别', '等级', '发布时间', '内容'])
                    for comment in self.sortedcomment:
                        writer.writerow([comment['member']['mid'], comment['member']['uname'], comment['member']['sex'],
                                         comment['member']['level_info']['current_level'],
                                         time.asctime(time.localtime(comment['ctime'])),
                                         comment['content']['message']])
                    print(f'已保存到{self.vidname}-{n}.csv')
                elif verbose == 3:
                    print('暂未开发')

                else:
                    print('参数错误，默认无格式保存全部内容，可能保存失败')
                    for comment in self.sortedcomment:
                        try:
                            writer.writerow(comment.items)
                        except Exception as e:
                            print('未知错误！')
                            print(repr(e))
        else:
            print('爬取完成，未保存')

    def run(self):
        allpagedict = self.request_json_dict()
        self.vidname = self.get_basic_info()
        self.users_level_ratio()
        self.save_as_csv()


if __name__ == '__main__':
    print('b站视频评论区查询姬')
    vid = input('输入视频AV号（不带av前缀的纯数字）或BV号(带BV前缀): ')  # 判断流程在构造函数
    pagenum = int(input('输入需要抓取的页数: '))
    mode = int(input('输入数字选择评论排序模式：\n1、按热度排序(默认)\n2、按时间排序'))
    spider = BilibiliCommentSpider(vid=vid, pagenum=pagenum,
                                   mode=mode if mode == 2 else 3)   # vid为纯数字av号(int)或以BV开头的bv号(str)
    spider.run()

