import time
import requests
import os


def println(content=''):
    try:
        width = os.get_terminal_size().columns // 2 - len(content) * 2 // 2
    except OSError:
        width = 25 - len(content) * 2 // 2
    print('%s%s%s' % ('-' * width, content, '-' * width))

println("BY 夏日夕暮 ")
println('登录')
username = input('请输入账号: ')
password = input('请输入密码: ')
res = requests.post('https://zjy2.icve.com.cn/dzx/portalApi/portallogin/login',
                    cookies={'verifycode': '457308D59BE06B262B798F9EF51A4C9F@637407653584698182'},
                    data={
                        'schoolId': 'qsi5aeooejtbsx9fwfhjra',
                        'userName': username,
                        'userPwd': password,
                        'verifyCode': 8830
                    })
information = res.json()
if information.get('code') == 1:
    println('登录成功')
    print('欢迎 %s 同学' % information['displayName'])
    println('选取课程')
else:
    print(information['msg'])

cookies = res.cookies
res = requests.get('https://zjy2.icve.com.cn/api/student/learning/getLearnningCourseList', cookies=cookies)
courseList = res.json()['courseList']
for i, course in enumerate(courseList):
    print('%i.%s' % (i, course.get('courseName')))
course = courseList[int(input('请输入需要刷课的序号: '))]
println('开始刷课')
# 获取课堂内容
res = requests.post('https://zjy2.icve.com.cn/api/study/process/getProcessList',
                    cookies=cookies,
                    data={'courseOpenId': course['courseOpenId'],
                          'openClassId': course['openClassId']
                          }
                    )
# 获取专题内容
for progress in res.json()['progress']['moduleList']:
    res = requests.post('https://zjy2.icve.com.cn/api/study/process/getTopicByModuleId',
                        cookies=cookies,
                        data={
                            'courseOpenId': course['courseOpenId'],
                            'moduleId': progress['id']}
                        )
    # 获取篇章内容
    for topic in res.json()['topicList']:
        print('%s' % topic['name'])
        res = requests.post('https://zjy2.icve.com.cn/api/study/process/getCellByTopicId',
                            cookies=cookies,
                            data={
                                'courseOpenId': course['courseOpenId'],
                                'openClassId': course['openClassId'],
                                'topicId': topic['id']
                                }
                            )
        for cell in res.json().get('cellList'):
            # 获取文章内容
            for i in range(5):
                view = requests.post('https://zjy2.icve.com.cn/api/common/Directory/viewDirectory',
                                     cookies=cookies,
                                     data={'courseOpenId': course['courseOpenId'],
                                           'openClassId': course['openClassId'],
                                           'cellId': cell['Id'],
                                           'flag': 's',
                                           'moduleId': progress.get('id')
                                           }
                                     ).json()
                if view.get('code') == -100:
                    requests.post('https://zjy2.icve.com.cn/api/common/Directory/changeStuStudyProcessCellData',
                                  cookies=cookies,
                                  data={
                                      'courseOpenId': course['courseOpenId'],
                                      'openClassId': course['openClassId'],
                                      'moduleId': progress['id'],
                                      'cellId': cell['Id'],
                                      'cellName': cell['cellName']
                                     }
                                  )
                    continue
                if 'guIdToken' not in view:
                    continue
                else:
                    break
            else:
                exit('获取文章信息异常')
            # 提交成功信息
            for i in range(5):
                res = requests.post('https://zjy2.icve.com.cn/api/common/Directory/stuProcessCellLog',
                                    cookies=cookies,
                                    data={
                                        'courseOpenId': course['courseOpenId'],
                                        'openClassId': course['openClassId'],
                                        'cellId': cell['Id'],
                                        'cellLogId': None,
                                        'picNum': view.get('pageCount', 0),
                                        'studyNewlyTime': view.get('audioVideoLong', 100),
                                        'studyNewlyPicNum': 0,
                                        'token': view['guIdToken']
                                        }
                                    ).json()
                print('\t%s %s ' % (cell['cellName'], res['msg']))
                if res['code'] == 1:
                    break
                else:
                    print('等待10秒...')
                    time.sleep(10)
            else:
                exit('提交数据异常')
            time.sleep(2)
