from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium import webdriver
import selenium

from bs4 import BeautifulSoup

import datetime
import json
import sys
import os

try:
    with open('config.json') as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    ecampus_id = input("ID: ")
    ecampus_password = input("Password: ")
    CONFIG = {
        "url": "https://ecampus.changwon.ac.kr",
        "id": ecampus_id,
        "password": ecampus_password
    }
    with open('config.json', 'w') as f:
        json.dump(CONFIG, f)


URL = CONFIG['url'] + '/login.php'
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--log-level=3')
options.add_argument('--disable-logging')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')

if getattr(sys, 'frozen', False):
    chromedriver_path = os.path.join(sys._MEIPASS, "chromedriver.exe")
    driver = webdriver.Chrome(
        executable_path=chromedriver_path, options=options)
else:
    driver = webdriver.Chrome(
        executable_path="chromedriver", options=options)

driver.implicitly_wait(3)
driver.get(url=URL)

driver.find_element_by_name('username').send_keys(CONFIG['id'])
driver.find_element_by_name('password').send_keys(CONFIG['password'])
driver.find_element_by_name('loginbutton').click()

courses_elements = driver.find_elements_by_css_selector(
    '#region-main > div > div.progress_courses > div.course_lists > ul > li > div')

courses = list()
# print("# 강좌 전체보기")
for course_elements in courses_elements:
    course = {}

    # Title
    course_name_element = course_elements.find_elements_by_css_selector(
        'a > div.course-name > div.course-title > h3')
    course['title'] = course_name_element[0].get_attribute('innerHTML')
    # print("[TITLE] " + course['title'])

    # Link
    course_link_element = course_elements.find_elements_by_css_selector('a')
    link = course_link_element[0].get_attribute('href')
    course['id'] = link[link.rfind('?id=')+4:]
    # print("[LINK] ecampus.changwon.ac.kr/course/view.php?id=" + course['id'])

    courses.append(course)

# Access Notice
driver.get(url=CONFIG['url'] + '/mod/ubboard/my.php')

notices = list()
posts_elements = driver.find_elements_by_css_selector(
    '#region-main > div > div.ubboard > div.ubboard_list > div.ubboard_container > div.list > table > tbody > tr')

for post_element in posts_elements:
    post_a_element = post_element.find_element_by_css_selector(
        'td:nth-child(2) > a')
    post_date_element = post_element.find_element_by_css_selector(
        'td:nth-child(4)')
    notice = {}
    notice['title'] = post_a_element.text
    notice['link'] = post_a_element.get_attribute('href')
    notice['date'] = post_date_element.text
    notices.append(notice)
    # print(notice['title'])

for course in courses:
    # view
    driver.get(
        url=CONFIG['url'] + '/course/view.php?id=' + course['id'])
    this_week_element = driver.find_elements_by_css_selector(
        '#region-main > div > div.course-content > div:nth-child(2) > ul > li')

    if this_week_element:
        # print("["+course['id']+":WEEKS] " +
        #       this_week_element[0].get_attribute('aria-label'))
        course['week'] = 6
        course['week-title'] = this_week_element[0].get_attribute('aria-label')

        instance_elements = this_week_element[0].find_elements_by_css_selector(
            'div.content > ul > li > div > div > div:nth-child(2) > div')

        instances = list()
        for instance_element in instance_elements:
            title_element = instance_element.find_element_by_css_selector(
                'a > span')

            instance_contents = title_element.text.split('\n')
            if len(instance_contents) > 1 and instance_contents[1] == '동영상':
                try:
                    time_element = instance_element.find_element_by_css_selector(
                        'span.displayoptions > span:nth-child(1)')
                    playtime_element = instance_element.find_element_by_css_selector(
                        'span.displayoptions > span:nth-child(2)')
                    instances.append({'title': title_element.text.split(
                        '\n')[0], 'time': time_element.text[1:], 'playtime': playtime_element.text[2:]})
                except:
                    playtime_element = instance_element.find_element_by_css_selector(
                        'span.displayoptions > span:nth-child(1)')
                    instances.append({'title': title_element.text.split(
                        '\n')[0], 'time': "", 'playtime': playtime_element.text[2:]})
                # print("[INSTANCE] " + instances[-1]['title'])
        course['instances'] = instances
    else:
        # print("["+course['id']+"] No Data")
        course['week'] = 0

    if course['week'] == 0:
        continue

    # user progress
    driver.get(
        url=CONFIG['url'] + '/report/ubcompletion/user_progress_a.php?id=' + course['id'])

    attendance_elements = driver.find_elements_by_css_selector(
        '#region-main > div > div:nth-child(3) > div > div:nth-child(2) > table > tbody > tr')

    attendances = {}
    for attendance_element in attendance_elements:
        if len(attendance_element.find_elements_by_css_selector('td')) == 6:
            weeks_num = int(attendance_element.find_elements_by_css_selector(
                'td:nth-child(1)')[0].text)
            attendances[weeks_num] = []
            attendance = {}
            attendance['title'] = attendance_element.find_elements_by_css_selector(
                'td:nth-child(2)')[0].text
            attendance['ox'] = attendance_element.find_elements_by_css_selector(
                'td:nth-child(5)')[0].text
            attendances[weeks_num].append(attendance)
        else:  # 4
            attendance = {}
            attendance['title'] = attendance_element.find_elements_by_css_selector(
                'td:nth-child(1)')[0].text
            attendance['ox'] = attendance_element.find_elements_by_css_selector(
                'td:nth-child(4)')[0].text
            attendances[weeks_num].append(attendance)
    course['attendances'] = attendances

    # Task
    driver.get(
        url=CONFIG['url'] + '/mod/assign/index.php?id=' + course['id'])

    tasks_elements = driver.find_elements_by_css_selector(
        '#region-main > div > table > tbody > tr')

    weeks = 1
    tasks = {weeks: []}
    for row_element in tasks_elements:
        td_elements = row_element.find_elements_by_css_selector('td')

        if len(td_elements) == 1:
            weeks += 1
            tasks[weeks] = []
        else:
            task = {}
            task['title'] = td_elements[1].text
            task['deadline'] = td_elements[2].text
            task['submit'] = td_elements[3].text
            tasks[weeks].append(task)

    course['tasks'] = tasks

print("※ 공지사항")
for notice in notices:
    print("[%s] %s" % (notice['date'], notice['title']))

now = datetime.datetime.now()
print("\n※ 이번 주차 출석 현황")
for course in courses:
    if course['week']:
        print("%s. %s" % (course['id'], course['title']))
        index = 0
        for instance in course['instances']:
            ox = course['attendances'][course['week']][index]['ox']
            index += 1
            print("  [%s] %s (%s) " %
                  (ox, instance['title'], instance['playtime']), end="")
            time = instance['time']
            if ox == 'X' and time != "":
                time = time[time.find('~')+2:time.find('(')-1]
                remain_time = datetime.datetime.strptime(
                    time, '%Y-%m-%d %H:%M:%S') - now
                remain_time_text = "%d일 %d시간" % (
                    remain_time.days, remain_time.seconds // 3600)
                print("[남은 시간 %s]" % (remain_time_text))
            else:
                print("")

        for task_contents in course['tasks'][course['week']]:
            if task_contents['submit'] == "제출 완료":
                print("    [O] %s" % (task_contents['title']))
            else:
                time = task_contents['deadline']
                remain_time = datetime.datetime.strptime(
                    time, '%Y-%m-%d %H:%M') - now
                remain_time_text = "%d일 %d시간" % (
                    remain_time.days, remain_time.seconds // 3600)
                print("    [X] %s [남은 시간 %s]" %
                      (task_contents['title'], remain_time_text))
