# by 夕迹
# QQ: 719893361

import random
import base64
import json
import os
import time

for i in range(3):
    try:
        import requests
        from Cryptodome.Cipher import DES
        from Cryptodome.Util import Padding
    except ModuleNotFoundError:
        os.system('pip3 install pycryptodomex')
        os.system('pip3 install requests')
    else:
        break
try:
    WINDOWS_WIDTH = os.get_terminal_size().columns
except OSError:
    WINDOWS_WIDTH = 50

HEADERS = {
    'Authorization': None,
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh',
    'UA-AUTHORIZATION': None,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
    'Content-Type': 'application/json',
}


def login():
    while 1:
        username = input('请输入用户名: ')
        password = input('请输入密码: ')
        response = requests.post(
            'https://www.ulearning.cn/umooc/user/login.do',
            data={
                'name': username,
                'passwd': password
            },
            allow_redirects=False
        )

        if 'token' in response.cookies:
            HEADERS['Authorization'] = response.cookies.get('token')
            HEADERS['UA-AUTHORIZATION'] = response.cookies.get('token')
            print('登录成功')
            return
        else:
            print('登录失败, 请手动登录官网检查账号状态')


def encryption(data):
    crypt = DES.new(b'12345678', DES.MODE_ECB)
    content = json.dumps(data, separators=(',', ':'))
    content = Padding.pad(content.encode('utf8'), 8, 'pkcs7')
    content = crypt.encrypt(content)
    content = base64.b64encode(content)
    return content


def learn():
    # 获取全部课程信息
    response = requests.get(
        'https://courseapi.ulearning.cn/courses/students?keyword=&publishStatus=1&type=1&pn=1&ps=15&lang=zh',
        headers=HEADERS
    )

    # 获取课程id列表,打印课程信息
    course_list = response.json()['courseList']
    print('-' * WINDOWS_WIDTH)
    for index, course in enumerate(course_list):
        print('%d. %s' % (index, course.get('name')))
    print('-' * WINDOWS_WIDTH)
    course = course_list[int(input('请输入需要刷课的序号: '))]

    # 获取courseID
    response = requests.get(
        f'https://courseapi.ulearning.cn/textbook/student/{course["id"]}/list?lang=zh',
        headers=HEADERS
    ).json()

    # 获取课程内容信息
    reg = requests.get(
        f'https://api.ulearning.cn/course/stu/{response[0]["courseId"]}/directory?classId={course["classId"]}',
        headers=HEADERS
    )

    # 循环遍历课程内容
    for index, chapter in enumerate(reg.json()['chapters']):
        data = {
            "itemid": None,
            "autoSave": 1,
            "version": None,
            "withoutOld": None,
            "complete": 1,
            "studyStartTime": int(time.time()),
            "userName": None,
            "score": 100,
            "page_study_record_dto_list": []
        }
        print('-' * WINDOWS_WIDTH)
        # 打印专题标题
        print('专题ID: %s\t%s' % (chapter.get('nodeid'), chapter.get('nodetitle')))
        page_study_record_dto_list = []
        for item in chapter.get('items'):
            print('\t章节ID: %s\t%s' % (item.get('itemid'), item.get('title')))
            data['itemid'] = item.get('itemid')
            for course_page in item.get('coursepages'):
                # 打印文章标题
                print('\t\t文章ID: %s\t%s' % (course_page.get('relationid'), course_page.get('title')))
                page_study_record_dto_list.append(
                    {
                        "pageid": course_page.get('relationid'),
                        "complete": 1,
                        "studyTime": random.randint(400, 800),
                        "score": 100,
                        "answerTime": 1,
                        "submitTimes": 0,
                        "questions": [],
                        "videos": [],
                        "speaks": []
                    }
                )
            data['page_study_record_dto_list'] = page_study_record_dto_list
            requests.post('https://api.ulearning.cn/yws/api/personal/sync?courseType=4&platform=PC',
                          headers=HEADERS,
                          data=encryption(data)
                          )

    print('已全部完成')
    print('-' * WINDOWS_WIDTH)


if __name__ == '__main__':
    while 1:
        login()
        learn()
