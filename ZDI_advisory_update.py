import os
import json 
import datetime
import requests
import feedparser
from lxml import etree
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

def download_advisory(url):
    print("Download:",url)
    response = requests.get(url)
    content = response.content
    if(response.url != url):
        return False

    tree = etree.HTML(content)
    date = tree.xpath('/html/body/section/div/div/data/text()')[0]
    title= tree.xpath('/html/body/section/div/div/h2/text()')[0]
    ID_1 = tree.xpath('/html/body/section/div/div/h3/text()[1]')[0]
    ID_2 = tree.xpath('/html/body/section/div/div/h3/text()[2]')[0]
    try:
        cveId = tree.xpath('/html/body/section/div/div/table/tr[1]/td[2]/a/text()')[0]
    except:
        cveId = ""
    baseScore = tree.xpath('/html/body/section/div/div/table/tr[2]/td[2]/text()')[0].strip()[:-1]
    try:
        vectorString = tree.xpath('/html/body/section/div/div/table//tr[2]/td[2]/a/text()')[0]
    except:
        vectorString = ""

    vendors = tree.xpath('/html/body/section/div/div/table/tr[3]/td[2]/*')[0].xpath('string(.)')
    products = tree.xpath('/html/body/section/div/div/table/tr[4]/td[2]/*')[0].xpath('string(.)')

    if tree.xpath('/html/body/section/div/div/table/tr[5]/td[1]/text()')[0].strip() == "TREND MICRO CUSTOMER PROTECTION":
        # print("skip \"TREND MICRO CUSTOMER PROTECTION\"")
        description =  '\n'.join(tree.xpath('/html/body/section/div/div/table/tr[6]/td[2]/p/text()'))
        addtionnal_details = tree.xpath('/html/body/section/div/div/table/tr[7]/td[2]')[0].xpath('string(.)').replace("\n                            ","").replace("\n                        ","").replace("\n                    ","")

        timeline=  '\n'.join(tree.xpath('/html/body/section/div/div/table/tr[8]/td[2]/ul/li/text()'))
        credit = tree.xpath('/html/body/section/div/div/table/tr[9]/td[2]/text()')[0]
    else:
        description =  '\n'.join(tree.xpath('/html/body/section/div/div/table/tr[5]/td[2]/p/text()'))
        addtionnal_details = tree.xpath('/html/body/section/div/div/table/tr[6]/td[2]')[0].xpath('string(.)').replace("\n                            ","").replace("\n                        ","").replace("\n                    ","")
        timeline=  '\n'.join(tree.xpath('/html/body/section/div/div/table/tr[7]/td[2]/ul/li/text()'))
        credit = tree.xpath('/html/body/section/div/div/table/tr[8]/td[2]/text()')[0]

    data = {"date":date,"title":title,"ID_1":ID_1,"ID_2":ID_2,"cveId":cveId,"baseScore":baseScore,"vectorString":vectorString,"vendors":vendors,"products":products,"description":description,"addtionnal_details":addtionnal_details,"timeline":timeline,"credit":credit}

    year = "20" + ID_1.split("-")[1]

    advisories_fold = os.path.join(os.path.dirname(__file__),"advisories/" + year)
    if not os.path.exists(advisories_fold):
        os.mkdir(advisories_fold)

    file_ptah = advisories_fold + "/" + ID_1 + ".json"
    print(file_ptah)
    with open(file_ptah,"w") as f:
        json.dump(data,f,indent=4,ensure_ascii=False)
    return True

def update():
    rss_url= "https://www.zerodayinitiative.com/rss/published/"
    response = requests.get(rss_url, timeout=20,verify=False)
    feed = feedparser.parse(response.content)

    for entry in feed.entries:
        d = entry.get('updated_parsed') or entry.get('published_parsed')
        pub_day = datetime.date(d[0], d[1], d[2])
        yesterday = datetime.date.today() + datetime.timedelta(-1)
        if pub_day == yesterday:
            title = entry.title
            link = entry.link
            if str(link).startswith("http://"):
                link = link.replace("http://","https://")
            download_advisory(link)

if __name__ == '__main__':
    update()
    print("Done!")
