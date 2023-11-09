# by 夕迹
# QQ: 719893361

import base64
import json
import random
import re
import requests

from abc import ABC, abstractmethod

from Cryptodome.Cipher import DES
from Cryptodome.Util import Padding


def encryption(data) -> str:
    """
    对payload加密
    """
    crypt = DES.new(b'12345678', DES.MODE_ECB)
    content = json.dumps(data, separators=(',', ':'))
    content = Padding.pad(content.encode('utf8'), 8, 'pkcs7')
    content = crypt.encrypt(content)
    content = base64.b64encode(content)
    return str(content, encoding='utf8')


# 定义抽象状态类
class State(ABC):
    """
    抽象类
    """
    @abstractmethod
    def handle(self, context):
        pass


class StateMachine:
    """
    状态机
    """
    def __init__(self):
        self.current_state = LoginState()

    def transition_to(self, new_state):
        self.current_state = new_state

    def execute(self):
        self.current_state.handle(self)


class LoginState(State):
    """
    登录状态
    """

    def handle(self, context: StateMachine):
        print('----------登录----------')
        username = input('请输入用户名: ')
        password = input('请输入密码: ')
        response = requests.post(
            'https://www.ulearning.cn/umooc/user/login.do',
            data={
                'name': username,
                'passwd': password
            },
            allow_redirects=False,
        )
        if 'token' in response.cookies:
            headers = {
                'Authorization': response.cookies.get('token'),
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'zh',
                'UA-AUTHORIZATION': response.cookies.get('token'),
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                              'Chrome/85.0.4183.121 Safari/537.36',
                'Content-Type': 'application/json',
            }
            context.transition_to(SelectClassState(headers))
            print('登录成功')
        else:
            print('登录失败, 请手动登录官网检查账号状态')


class SelectClassState(State):
    """
    选择课程
    """

    def __init__(self, headers: dict):
        self.headers = headers

    def handle(self, context: StateMachine):
        # 获取课程信息
        response = requests.get(
            url='https://courseapi.ulearning.cn/courses/students?keyword=&publishStatus=1&type=1&pn=1&ps=15&lang=zh',
            headers=self.headers
        ).json()
        print('----------选择课程----------')
        # 打印课程列表
        course_list = response['courseList']
        for selected_index, course in enumerate(course_list):
            print('%d. %s' % (selected_index, course.get('name')))
        print(
            'l. 重新登录\n'
            'q. 退出'
        )
        # 选择课程序号
        raw_input = input(': ').strip()
        if raw_input == 'q':
            exit()
        if raw_input == 'l':
            context.transition_to(LoginState())
            return
        if not re.match(r'^\d+$', raw_input):
            print('输入错误，请重新输入')
            return
        selected_index = int(raw_input)
        if len(course_list) <= selected_index:
            print('输入错误，请重新输入')
            return
        course = course_list[int(raw_input)]
        response = requests.get(
            url=f'https://courseapi.ulearning.cn/textbook/student/{course["id"]}/list?lang=zh',
            headers=self.headers
        ).json()
        context.transition_to(GetChapterState(self.headers, course['classId'], response[0]["courseId"]))
        return True


class GetChapterState(State):
    """
    获取全部章节
    """
    def __init__(self, headers, class_id, course_id):
        self.headers = headers
        self.class_id = class_id
        self.course_id = course_id

    def handle(self, context):
        # 获取课程内容信息
        data = requests.get(
            url=f'https://api.ulearning.cn/course/stu/{self.course_id}/directory?classId={self.class_id}',
            headers=self.headers
        ).json()
        context.transition_to(DurationState(self.headers, self.class_id, self.course_id, data['chapters']))


class DurationState(State):
    """
    需要学习的时间
    """

    def __init__(self, headers, class_id, course_id, chapters):
        self.headers = headers
        self.class_id = class_id
        self.course_id = course_id
        self.chapters = chapters

    def handle(self, context):
        print('----------设置学习时间----------')
        raw_input = input('请输入所需总时长, 例如[100-400或100]秒: ')
        if re.match(r'^\d+-\d+$', raw_input):
            start, end = raw_input.split('-')
            lean_duration = random.randint(int(start), int(end))
        elif re.match(r'^-?\d+', raw_input):
            lean_duration = int(raw_input)
        else:
            print('输入错误')
            return
        context.transition_to(SelectChapterState(
            self.headers,
            self.class_id,
            self.class_id,
            self.chapters,
            lean_duration
        ))


class SelectChapterState(State):
    """
    选择章节
    """

    def __init__(self, headers, class_id, course_id, chapters, lean_duration):
        self.headers = headers
        self.class_id = class_id
        self.course_id = course_id
        self.chapters = chapters
        self.lean_duration = lean_duration

    def handle(self, context: StateMachine):
        print('----------设置学习章节----------')
        for index, chapter in enumerate(self.chapters):
            print(f"{index}. {chapter['nodetitle']}")
        raw_input = input('请输入需要跳过的专题序号[多个请用“,”分开。留空则刷全部] : ')
        if not re.match(r'^(?:(\d)+,?)*$', raw_input):
            print('输入错误')
            return
        skip_items = {int(n.strip()) for n in raw_input.split(',') if n}
        lean_items = {n for n in range(len(self.chapters))} - skip_items
        chapters = [self.chapters[i] for i in lean_items]
        context.transition_to(ShowSettingState(
            self.headers,
            self.class_id,
            self.course_id,
            self.chapters,
            self.lean_duration,
            chapters,
            lean_items
        ))


class ShowSettingState(State):
    def __init__(self, headers, class_id, course_id, chapters_all, lean_duration, chapters_lean, lean_items):
        """
        @param headers          请求头
        @param class_id         课程id
        @param course_id        不知道是啥
        @param chapters_all     全部章节
        @param chapters_lean    学习章节
        @param lean_duration    学习总时长
        @param lean_items       欲学习章节
        """
        self.headers = headers
        self.class_id = class_id
        self.course_id = course_id
        self.chapters_all = chapters_all
        self.chapters_lean = chapters_lean
        self.need_time = lean_duration
        self.lean_items = lean_items

    def handle(self, context):
        print('--------查看设置----------')
        print(f'设置学习时长: {self.need_time}秒')
        print(f'设置学习章节: {",".join(str(n) for n in self.lean_items)}')
        raw_input = input(
            'r. 重新设置\n'
            's. 选择课程\n'
            't. 开始学习\n'
            'l. 重新登录\n'
            'q. 退出\n'
            ':'
        ).strip()
        if raw_input == 'r':
            context.transition_to(DurationState(self.headers, self.class_id, self.course_id, self.chapters_all))
        elif raw_input == 's':
            context.transition_to(SelectClassState(self.headers))
        elif raw_input == 't':
            section_count = 0
            for chapter in self.chapters_lean:
                for item in chapter['items']:
                    for _ in item['coursepages']:
                        section_count += 1
            mean_time = self.need_time // section_count
            context.transition_to(CourseLearnerState(self.headers, self.chapters_lean, mean_time))
        elif raw_input == 'l':
            context.transition_to(LoginState())
        elif raw_input == 'q':
            exit()
        else:
            print('输入错误')


class CourseLearnerState(State):
    def __init__(self, headers, chapters, mean_time):
        self.headers = headers
        self.chapters = chapters
        self.mean_time = mean_time

    def handle(self, context):
        for chapter in self.chapters:
            print(f'ID: {chapter["id"]} 专题: {chapter["nodetitle"]}')
            for item in chapter['items']:
                data = {
                    "itemid": item['itemid'],
                    "autoSave": 1,
                    "version": None,
                    "withoutOld": None,
                    "complete": 1,
                    "studyStartTime": self.mean_time,
                    "userName": None,
                    "score": 100,
                    "page_study_record_dto_list": []
                }
                print(f'    ID: {item["itemid"]} 章节: {item["title"]}')
                for course in item['coursepages']:
                    relation = {
                        "pageid": course['relationid'],
                        "complete": 1,
                        "studyTime": self.mean_time,
                        "score": 100,
                        "answerTime": 1,
                        "submitTimes": 0,
                        "questions": [],
                        "videos": [],
                        "speaks": []
                    }
                    data["page_study_record_dto_list"].append(relation)
                    print(f'        ID: {course["relationid"]} 标题: {course["title"]} 学习时长: {self.mean_time}')
                # 提交请求
                requests.post(
                    url='https://api.ulearning.cn/yws/api/personal/sync?courseType=4&platform=PC',
                    headers=self.headers,
                    data=encryption(data)
                )
        context.transition_to(SelectClassState(self.headers))


def task():
    state = StateMachine()
    while True:
        state.execute()


if __name__ == '__main__':
    task()
