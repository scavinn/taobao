from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re,pymongo
from pyquery import PyQuery as pq

client = pymongo.MongoClient('localhost',27017)
db = client['taobao']
sheet = db['MS_products']

browser = webdriver.PhantomJS(executable_path=r'F:\phantomjs\bin\phantomjs.exe',service_args = ['--load-images=false'])
wait = WebDriverWait(browser,10)

browser.set_window_size(1400,900)

def search():
    '''
    定义search方法，找到‘搜索框’、‘提交’、‘总共页数’的位置
    '''
    print('正在搜索')
    try:
        browser.get('https://www.taobao.com')
        input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#q')))
        sumit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_TSearchForm > div.search-button > button')))
        input.clear()
        input.send_keys('美食')
        sumit.click()
        total = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.total')))        # 总共页数的标签位置
        get_products()      #这是首页，调用获取商品函数
        return total.text
    except TimeoutException:
        return search()

def next_page(page_num):
    '''
    定义翻页函数，找到’输入页数文本框‘、’确定按钮‘位置
    '''
    print('正在翻页',page_num)
    try:
        input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.form > input')))
        sumit = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
        input.clear()
        input.send_keys(page_num)
        sumit.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_num)))       # 判断所输入页数正好处于span标签中
        get_products()      #调用获取商品函数
    except TimeoutException:
        next_page(page_num)

def get_products():
    '''
    用pyquery解析网页源代码，获取商品
    '''
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist .items .item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()   #items方法获取.item下所有内容
    for item in items:
        product = {
            'image':item.find('.pic .img').attr('src'),
            'price':item.find('.price').text(),
            'deal':item.find('.deal-cnt').text()[:-3],
            'title':item.find('.title').text(),
            'shop':item.find('.shop').text(),
            'location':item.find('.location').text()
        }
        print(product)
        save_to_mongo(product)

def save_to_mongo(result):
    '''
    存储到mongoDB
    '''
    try:
        if sheet.insert(result):
            print('存储成功',result)
    except Exception:
        print('存储失败',result)

#运行主程序
def main():
    total = search()
    total = int(re.compile('(\d+)').search(total).group(1))     #用正则匹配总共页数
    # print(total)
    for i in range(2,total + 1):
        next_page(i)        #从第二页开始，调用翻页函数，依次翻页
    browser.close()

if __name__ == '__main__':
    main()
