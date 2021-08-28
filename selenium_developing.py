from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import requests
from tqdm import tqdm
import argparse
from lxml import etree
from mail import Email #如果不用科大邮箱，mail.py取最新一封邮件的代码可能也要改。科大邮箱默认最新未读邮件索引是1

parser = argparse.ArgumentParser(description='Ustc-course Spyder')
parser.add_argument('login', help='email address or github name', type=str)
parser.add_argument('password', help='your password of GitHub', type=str)
parser.add_argument('mailpassword', help='your password of your USTC email', type=str)
args = parser.parse_args()
GitAccount=args.login #github账户
GitPasswd=args.password #github密码
EmailAccount=args.login #邮箱账户，如果Chrome登录github不需要验证则可以放空
EmailPasswd=args.mailpassword #邮箱密码
names=['数据结构','structure'] #匹配条件，即合格的文件名必须至少包含列表中的一个字符串，这是为了防止中英文、习惯用语等导致的不匹配
search='ustc course' #搜索关键字，这里是ustc+course，一般不用改，要是想搜其他仓库也可以改（本程序可以搜的不仅仅是课程资料）
search=search.replace(' ','+') #转换成url要求的格式
req_timeout=20
content=''

option = webdriver.ChromeOptions()
option.add_argument('headless')# 添加无头模式
option.add_experimental_option('excludeSwitches', ['enable-logging'])
driver = webdriver.Chrome(options=option)
driver.implicitly_wait(req_timeout)

#登录github
session=requests.Session()
form=session.get('https://github.com/login').text
form=etree.HTML(form)
authenticity_token=form.xpath('.//input[@name="authenticity_token"]/@value')
timestamp=form.xpath('.//input[@name="timestamp"]/@value')
timestamp_secret=form.xpath('.//input[@name="timestamp_secret"]/@value')
field=form.xpath('.//input[@type="text" and contains(@name,"required")]/@name')
data={
    "commit": "Sign in",
    "trusted_device": "",
    "webauthn-support": "supported",
    "webauthn-iuvpaa-support": "unsupported",
    "return_to": "https://github.com/login",
    "allow_signup":"",
    "client_id":"",
    "integration":"",
    "authenticity_token":authenticity_token[0],
    "timestamp":timestamp[0],
    "timestamp_secret":timestamp_secret[0],
    "login":args.login,
    "password":args.password,
    field[0]:""
}
text=session.post('https://github.com/session',data=data).text

#输入邮箱验证码
if 'Device verification code' in text:
    text=etree.HTML(text)
    authenticity_token=text.xpath('.//input[@name="authenticity_token"]/@value')
    email = args.login
    password = args.mailpassword
    pop3_server = "mail.ustc.edu.cn" #如果不用科大邮箱，这里要改
    LT=None
    while LT==None:
        LT=Email(email,password,pop3_server).get_LT()
    data={'authenticity_token':authenticity_token[0],
          'otp':LT}
    session.post('https://github.com/sessions/verified-device',data=data)
    
cookies=session.cookies.get_dict()
for k,v in cookies.items():
    driver.add_cookie({"name":k,"value":v})
    
#搜索仓库
for page in tqdm(range(0,20),ncols=70,leave=False):
    url='https://github.com/search?p='+str(page+1)+'&q='+search+'&type=Repositories'
    driver.get(url)
    text=driver.page_source
    html=etree.HTML(text)
    repo=html.xpath('.//a[@class="v-align-middle"]/@href')
    for href in tqdm(repo,ncols=70,leave=False):
        driver.get('https://github.com'+href)
        text=driver.page_source
        html=etree.HTML(text)
        branch=html.xpath('.//span[@class="css-truncate-target"]/text()')
        if(len(branch)==0): #空仓库没有branch
            continue
        driver.get('https://github.com'+href+'/find/'+branch[0])
        text=driver.page_source
        html=etree.HTML(text)
        data_url=html.xpath('.//fuzzy-list[@class="js-tree-finder"]/@data-url') #获取完整文件列表
        driver.get('https://github.com'+data_url[0]) #获取所有目录
        text=driver.find_element_by_xpath('.//pre').text
        text=text.lower()
        for name in names:
            if name in text:
                with open('findings.txt','a') as fd:
                    fd.write('https://github.com'+href+'\n')
                break
