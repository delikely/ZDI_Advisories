import os
import json
import datetime
import re
import requests
import feedparser
from lxml import etree
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

def download_advisory(url):
    print("Download:", url)
    response = requests.get(url)
    content = response.content
    if response.url != url:
        return False

    tree = etree.HTML(content)

    # --- Metadata column (left sidebar) ---
    # Date: inside the inline-flex div with calendar icon
    date = tree.xpath('//span[contains(@class,"text-zdi-blue") and contains(@class,"uppercase") and contains(@class,"tracking-widest")]/text()')[0].strip()
    # Title: the <h1> tag
    title = tree.xpath('//h1/text()')[0].strip()

    # ZDI ID (e.g. ZDI-26-397) — first metadata-value span
    ID_1 = tree.xpath('//span[@class="metadata-value"]/text()')[0].strip()
    # ZDI-CAN ID (e.g. ZDI-CAN-30168) — second metadata-value span
    ID_2 = tree.xpath('//span[contains(@class,"metadata-value") and contains(@class,"text-gray-400")]/text()')[0].strip()

    # CVE ID — link inside metadata row labelled "CVE ID"
    try:
        cveId = tree.xpath('//p[text()="CVE ID"]/following-sibling::span//a/text()')[0].strip()
    except (IndexError, AttributeError):
        cveId = ""

    # CVSS Score — metadata-value with "rounded" class, after "CVSS Score" label
    baseScore = tree.xpath('//p[text()="CVSS Score"]/following-sibling::div//span[contains(@class,"metadata-value") and contains(@class,"rounded")]/text()')[0].strip()
    # CVSS Vector String — link inside the same CVSS Score row
    try:
        vectorString = tree.xpath('//p[text()="CVSS Score"]/following-sibling::div//a/text()')[0].strip()
    except (IndexError, AttributeError):
        vectorString = ""

    # Affected Vendors — text content after "Affected Vendors" label
    vendors = tree.xpath('//p[text()="Affected Vendors"]/following-sibling::span//text()')
    vendors = ' '.join(v.strip() for v in vendors if v.strip())

    # Affected Products — text content after "Affected Products" label
    products = tree.xpath('//p[text()="Affected Products"]/following-sibling::span//text()')
    products = ' '.join(p.strip() for p in products if p.strip())

    # --- Content area (right side) ---
    # Check for "TREND MICRO CUSTOMER PROTECTION" section
    has_tm = tree.xpath('//h3[contains(text(),"TREND MICRO CUSTOMER PROTECTION")]')

    # Description: <p> tags between "Vulnerability Details" and next <h3>
    description = '\n'.join(
        tree.xpath('//h3[text()="Vulnerability Details"]/following-sibling::p[not(preceding-sibling::h3[text()="Additional Details"])]/text()')
    )

    # Additional Details: content between "Additional Details" heading and "Disclosure Timeline"
    addtionnal_details_nodes = tree.xpath(
        '//h3[text()="Additional Details"]/following-sibling::p[not(preceding-sibling::h3[text()="Disclosure Timeline"])]'
    )
    addtionnal_details = '\n'.join(node.xpath('string(.)').strip() for node in addtionnal_details_nodes)
    # Collapse HTML indentation whitespace
    addtionnal_details = re.sub(r'\n[\s\t\n]+', '\n', addtionnal_details).strip()

    # Disclosure Timeline: <li> items after "Disclosure Timeline" heading
    timeline_nodes = tree.xpath('//h3[text()="Disclosure Timeline"]/following-sibling::ul/li')
    timeline = '\n'.join(node.xpath('string(.)').strip() for node in timeline_nodes)

    # Credit: <p> text after "Credit" heading
    credit = tree.xpath('//h3[text()="Credit"]/following-sibling::p/text()')
    credit = ' '.join(c.strip() for c in credit if c.strip()) if credit else ""

    data = {"date":date,"title":title,"ID_1":ID_1,"ID_2":ID_2,"cveId":cveId,"baseScore":baseScore,"vectorString":vectorString,"vendors":vendors,"products":products,"description":description,"addtionnal_details":addtionnal_details,"timeline":timeline,"credit":credit}

    year = "20" + ID_1.split("-")[1]

    advisories_fold = os.path.join(os.path.dirname(__file__),"advisories/" + year)
    if not os.path.exists(advisories_fold):
        os.mkdir(advisories_fold)

    file_ptah = advisories_fold + "/" + ID_1 + ".json"
    print(file_ptah)
    with open(file_ptah,"w",encoding='utf-8') as f:
        json.dump(data,f,indent=4,ensure_ascii=False)
    return True

def update():
    rss_url = "https://www.zerodayinitiative.com/rss/published/"
    response = requests.get(rss_url, timeout=20, verify=False)
    feed = feedparser.parse(response.content)

    base_dir = os.path.join(os.path.dirname(__file__), "advisories")
    downloaded = 0
    skipped = 0

    for entry in feed.entries:
        link = entry.link
        if str(link).startswith("http://"):
            link = link.replace("http://", "https://")

        # Extract ZDI-ID from URL (e.g. ZDI-26-397)
        match = re.search(r'(ZDI-\d+-\d+)', link)
        if not match:
            continue
        zdi_id = match.group(1)
        year = "20" + zdi_id.split("-")[1]

        # Skip if already downloaded
        file_path = os.path.join(base_dir, year, zdi_id + ".json")
        if os.path.exists(file_path):
            skipped += 1
            continue

        print(f"Missing: {zdi_id}")
        if download_advisory(link):
            downloaded += 1

    print(f"Downloaded: {downloaded}, Skipped (existing): {skipped}")

if __name__ == '__main__':
    update()
    print("Done!")
