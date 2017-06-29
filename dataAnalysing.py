# coding=utf-8
# pip install requests
# pip install bs4
# pip install XlsxWriter
import re
import json
import requests
import xlsxwriter
from bs4 import BeautifulSoup
from collections import Counter


url = "https://www.lagou.com/jobs/positionAjax.json?needAddtionalResult=false"
keyword = input('请输入您所需要查找的关键字：')


headers = {
    'Host': "www.lagou.com",
    'Connection': "keep-alive",
    'Origin': "https://www.lagou.com",
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
    'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
    'Accept': "application/json, text/javascript, */*; q=0.01",
    'Referer': "https://www.lagou.com/jobs/list_python?labelWords=&fromSearch=true&suginput=",
    'Accept-Encoding': "gzip, deflate, br",
    'Accept-Language': "zh-CN,zh;q=0.8",
    'Cookie': "user_trace_token=20170606111150-5b540fff92f74297b9f81b625022fd65; LGUID=20170606111151-e2800df0-4a65-11e7-98e9-5254005c3644; JSESSIONID=ABAAABAACDBAAIAA787EE14DEED3D43CE2E828C247EC51B; _putrc=352547A3D72879DC; PRE_UTM=; PRE_HOST=; PRE_SITE=https%3A%2F%2Fwww.lagou.com%2Fjobs%2F3093276.html; PRE_LAND=https%3A%2F%2Fwww.lagou.com%2F; login=true; unick=%E7%AB%A5%E5%A5%8E; showExpriedIndex=1; showExpriedCompanyHome=1; showExpriedMyPublish=1; hasDeliver=9; _gid=GA1.2.89637083.1498032501; Hm_lvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1496970234,1498032500,1498032518,1498701331; Hm_lpvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1498724671; _ga=GA1.2.195518139.1496718696; LGSID=20170629162425-5c60b3e6-5ca4-11e7-9eae-525400f775ce; LGRID=20170629162430-5fc2f95a-5ca4-11e7-9f8f-5254005c3644; TG-TRACK-CODE=index_search; SEARCH_ID=cf65beb377eb416f84a0a44fa0ef4c6b; index_location_city=%E6%B7%B1%E5%9C%B3"
}


def get_jobs(url, pn=1, kw=keyword):

    data = {"first":"false", "pn":pn, "kd":kw}
    r = requests.post(url, data=data, headers=headers)
    jobs_data = r.json()
    return jobs_data
    # jobs_data = jobs_data["content"]["positionResult"]["result"]

    # for i in jobs_data:
    #     print(i["companyFullName"])
    #     print(i["city"])
    #     print(i["companyLabelList"])
    #     print(i["workYear"])
    #     print(i["education"])
    #     print(i["salary"])
    #     job_url = "https://www.lagou.com/jobs/" + str(i["positionId"]) + ".html"
    #     print(job_url)

def get_max_page(jobs):
    max_page_num = jobs['content']['pageSize']
    max_page_num = 30 if max_page_num > 30 else max_page_num
    return max_page_num

def read_id(jobs):
    tag = 'positionId'
    page_json = jobs['content']['positionResult']['result']
    company_list = []
    for i in range(15):
        company_list.append(page_json[i].get(tag))
    return company_list

def get_content(company_id):
    job_url = "https://www.lagou.com/jobs/{0}.html".format(company_id)
    r = requests.get(job_url,headers=headers)
    return r.text

def get_result(content):
    soup = BeautifulSoup(content, "html.parser")
    job_description = soup.select('dd[class="job_bt"]')
    job_description = str(job_description[0])
    rule = re.compile(r'<[^>]+>')
    result = rule.sub('', job_description)
    return result

def search_skill(result):
    rule = re.compile(r'[a-zA-Z]+')
    skill_list = rule.findall(result)
    return skill_list

def count_skill(skill_list):
    for i in range(len(skill_list)):
        skill_list[i] = skill_list[i].lower()
    count_dict = Counter(skill_list).most_common(80)
    return count_dict

def save_excel(count_dict, file_name):
    book = xlsxwriter.Workbook(
        r'/home/docker/{0}.xls'.format(file_name))
    tmp = book.add_worksheet()
    row_num = len(count_dict)
    for i in range(1, row_num):
        if i == 1:
            tag_pos = 'A%s' % i
            tmp.write_row(tag_pos, ['关键词', '频次'])
        else:
            con_pos = 'A%s' % i
            k_v = list(count_dict[i - 2])
            tmp.write_row(con_pos, k_v)
    chart1 = book.add_chart({'type': 'area'})
    chart1.add_series({
        'name': '=Sheet1!$B$1',
        'categories': '=Sheet1!$A$2:$A$80',
        'values': '=Sheet1!$B$2:$B$80'
    })
    chart1.set_title({'name': '关键词排名'})
    chart1.set_x_axis({'name': '关键词'})
    chart1.set_y_axis({'name': '频次(/次)'})
    tmp.insert_chart('C2', chart1, {'x_offset': 15, 'y_offset': 10})
    book.close()



if __name__ == '__main__':
    jobs = get_jobs(url, pn=2, kw=keyword)
    max_page = get_max_page(jobs)
    fin_skill_list = []
    # for page in range(1, max_page+1):
    for page in range(1):
        print('-----开始抓取信息-----')
        jobs = get_jobs(url, pn=page, kw=keyword)
        company_list = read_id(jobs)
        for company_id in company_list:
            content = get_content(company_id)
            result = get_result(content)
            skill_list = search_skill(result)
            fin_skill_list.extend(skill_list)
    print('-----结束抓取信息-----')        
    print('-----开始统计关键字出现频率-----')
    count_dict = count_skill(fin_skill_list)
    print('-----结束统计关键字出现频率-----')
    file_name = input('请输入要保持文件名：')
    save_excel(count_dict, file_name)
    print('-----保存完成----')

    
    
    
    
    