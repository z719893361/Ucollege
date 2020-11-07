# 作者 by 夕迹
# QQ: 719893361
import random
import base64
import json

try:
    import requests
    from Cryptodome.Cipher import DES
    from Cryptodome.Util import Padding
except ModuleNotFoundError:
    import os
    os.system('pip install pycryptodomex')
    os.system('pip install requests')


HEADERS = {
    'Authorization': None
}


def login():
    while 1:
        username = input('请输入用户名: ')
        password = input('请输入密码: ')
        reg = requests.post('https://www.ulearning.cn/umooc/user/login.do', data={
            'name': username,
            'passwd': password
        }, allow_redirects=False)
        if 'token' in reg.cookies:
            HEADERS['Authorization'] = reg.cookies.get('token')
            print('登录成功')
            return
        else:
            print('登录失败, 请手动登录官网检查账号状态')


def encryption(data):
    crypt = DES.new(b'12345678', DES.MODE_ECB)
    content = json.dumps(data, separators=(',', ':'))
    content = Padding.pad(content.encode('utf8'), 16, 'pkcs7')
    content = crypt.encrypt(content)
    content = base64.b64encode(content)
    return content


def learn():
    res = requests.get('https://courseapi.ulearning.cn/courses/students?keyword=&publishStatus=1&type=1&pn=1&ps=15&lang=zh',
                       headers=HEADERS)
    courseList = []
    print('-' * 50)
    for i, course in enumerate(res.json().get('courseList')):
        courseList.append(course.get('classId'))
        print('%d. %s' % (i, course.get('name')))
    print('-' * 50)
    data = {
        "itemid": None,
        "autoSave": 1,
        "version": None,
        "withoutOld": None,
        "complete": 1,
        "studyStartTime": 0,
        "userName": None,
        "score": 100,
        "pageStudyRecordDTOList": []
    }
    reg = requests.get('https://api.ulearning.cn/course/stu/23138/directory?classId=%d' % courseList[int(input('请输入需要刷课的序号: '))],
                       headers=HEADERS)
    # 循环遍历JSON内容
    for i, chapter in enumerate(reg.json()['chapters']):
        # 打印专题标题
        print('专题ID: %s\t%s' % (chapter.get('nodeid'), chapter.get('nodetitle')))
        pageStudyRecordDTOList = []
        for item in chapter.get('items'):
            print('\t分节ID: %s\t%s' % (item.get('itemid'), item.get('title')))
            data['itemid'] = item.get('itemid')
            for coursepage in item.get('coursepages'):
                # 打印文章标题
                print('\t\t文章ID: %s\t%s' % (coursepage.get('relationid'), coursepage.get('title')))
                pageStudyRecordDTOList.append(
                    {
                        "pageid": coursepage.get('relationid'),
                        "complete": 1,
                        "studyTime": random.randint(1000, 3000),
                        "score": 100,
                        "answerTime": 0,
                        "submitTimes": 0,
                    }
                )
            data['pageStudyRecordDTOList'] = pageStudyRecordDTOList
            requests.post('https://api.ulearning.cn/yws/api/personal/sync?courseType=4&platform=PC',
                          headers=HEADERS,
                          data=encryption(data))
    print('已全部完成')
    print('-' * 50)


if __name__ == '__main__':
    while 1:
        login()
        learn()
