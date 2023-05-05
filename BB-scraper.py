from bs4 import BeautifulSoup
import json
import csv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import random
import time

from selenium.webdriver.common.action_chains import ActionChains

class BBScraper():

    def __init__(self):
        self.current_path = os.getcwd()
        self.driver_path = os.path.join(os.getcwd(), 'chromedriver')
        self.driver = webdriver.Chrome(executable_path = self.driver_path)
        self.driver.implicitly_wait(30)
        self.base_url = "https://www.bigbasket.com"
        self.headers = {
            'authority': 'www.bigbasket.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            #   'cache-control': 'max-age=0',
            #   'cookie': '_bb_locSrc=default; _bb_cid=1; _bb_hid=1723; _bb_vid="NTIzNzAxMTczOA=="; _bb_tc=0; _bb_aid="Mjk2NTE4NTMwNA=="; _bb_rdt="MzExMzQ5MDcxMA==.0"; _bb_rd=6; _sp_van_encom_hid=1722; _sp_bike_hid=1720; sessionid=9e52k1mzkt2u8fya8mwdd5l6ftmrbp60; jarvis-id=aeb31928-cd9a-4011-8708-92c9240d7bf7; _gid=GA1.2.741341646.1683125844; adb=0; bigbasket.com=66a0be9c-9d6f-4109-bbd0-697dcb9deb35; _gcl_au=1.1.428485076.1683125845; _fbp=fb.1.1683125846561.1739330889; ufi=1; _clck=1pffqau|1|fbb|0; _client_version=2663; csrftoken=Jv8fkzfcWZUOSIdERrnB3x0fL6Pr70L7qoxBlQLZBpaKtWwnQG4mU5QSe7OHlkp8; csurftoken=R2G8Sg.NTIzNzAxMTczOA==.1683203556602.5Cg4jW5YRzNMaOhWrtwrPQHpBrawuQ6lqGbtG4WYeS4=; _gat_gtag_UA_27455376_1=1; _gat_UA-27455376-1=1; _ga=GA1.1.233613085.1683125844; _ga_FRRYG5VKHX=GS1.1.1683203556.4.1.1683203558.58.0.0; _clsk=igbm70|1683203559034|2|1|p.clarity.ms/collect; ts="2023-05-04 18:02:39.427"; _bb_aid="Mjk2NTE4NTMwNA=="; _bb_cid=1; _bb_rd=6; csurftoken=OOKmVQ.NTIzNzAxMTczOA==.1683206227794.Mv9KuF/Tqhf23ZlNVJMqFjq9pDwAV6LDp3UXEYDJ/YQ=; ts="2023-05-04 18:47:09.826"; csrftoken=iMqYNtf1SkecpzbPS2QK9dJNgqhyPpl83q4KDXNp0yhgrIeT3iritGXGzexmPMY0',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
            }

    def interceptor(self,request):
        request.headers =  self.headers

    def page_load(self,url_tail=""):
        """
        Load the url in the driver
        """
        driver = self.driver
        # driver.request_interceptor = self.interceptor 
        delay = 3 
        driver.get(self.base_url+url_tail)
        time.sleep(2)

    def hover(self, element):
        hover = ActionChains(self.driver).move_to_element(element)
        hover.perform()

    def get_category_list0(self):
        hover_elem = self.driver.find_element(By.CSS_SELECTOR,"#navbar > ul > li.dropdown.full-wid.hvr-drop")
        self.hover(hover_elem)
        html_source = self.driver.page_source
        soup = BeautifulSoup(html_source,'html.parser')
        body = soup.find("body")
        category_list = body.find(class_ = 'container pad-0').find("ul",{"class":"dropdown-menu"}).find("ul",{"id":"navBarMegaNav"})

        x=[]
        for item in category_list.find_all("li"):
            x.append([item.find("a").getText(),item.find("a").get("href")])
        print(x)
        return x

    def get_category_list(self):
        hover_elem = self.driver.find_element(By.CSS_SELECTOR,"#navbar > ul > li.dropdown.full-wid.hvr-drop")
        self.hover(hover_elem)
        click_elem = self.driver.find_element(By.CSS_SELECTOR,'#navBarMegaNav > li:nth-child(12) > a')
        click_elem.click()
        html_source = self.driver.page_source
        soup = BeautifulSoup(html_source,'html.parser')
        body = soup.find("body")
        container = body.find(class_ = 'uiv2-myaccount-wrapper uiv2-mar-t-35 uiv2-search uiv2-all-categories-wrapper')
        super_category_list = container.select("div.dp_headding")
        category_list = container.select("div.uiv2-search-category-listing-cover")
        super_category_dict_p0 = {}
        for i, e in enumerate(category_list):
            cat_list = e.select("div.uiv2-search-cover")
            cat_dict_p1 = {}
            for cat in cat_list:
                name = cat.select_one("span").text
                sub_cat_dict_p2={}
                for sub_cat in cat.select("ul > li > a"):
                    sub_cat_name = sub_cat.text
                    sub_cat_link = sub_cat.get("href")
                    sub_cat_dict_p2[sub_cat_name] = sub_cat_link
                cat_dict_p1[name] = sub_cat_dict_p2
            super_category_dict_p0[super_category_list[i].text] = cat_dict_p1
        return super_category_dict_p0

    def get_product_data_from_list(self):
        """
        Get the product data
        """
        html_source = self.driver.page_source
        soup = BeautifulSoup(html_source,'html.parser')
        container = soup.select_one("#dynamicDirective > product-deck > section > div.col-md-9.wid-fix.clearfix.pl-wrap")
        breadcrumbs = soup.select_one("body > div.body-wrap > div.container.breadCrumbs.hidden-xs.hidden-sm.ng-scope > div")
        super_cat = breadcrumbs.select("div.breadcrumb-item")[1].select_one("span").text
        cat = breadcrumbs.select("div.breadcrumb-item")[2].select_one("span").text
        sub_cat = breadcrumbs.select("div")[3].select_one("span").text
        item_list = container.find(class_ = "items").find_all(class_ = "item")

        #to scrape data of first 10 products from each s
        n = 10 if len(item_list) > 10 else len(item_list)
        for i in range (0,n):
            item = item_list[i]
            product_elem = item.select_one("product-template > div")
            image  = product_elem.select_one("div:nth-of-type(3) > a > img").get("src")

            details_elem = product_elem.select_one("div:nth-of-type(4)")
            brand = details_elem.select_one("div.col-sm-12.col-xs-7.prod-name > h6").text
            name = details_elem.select_one("div.col-sm-12.col-xs-7.prod-name > a").text
            link =  details_elem.select_one("div.col-sm-12.col-xs-7.prod-name > a").get("href")
            id = link.split("/")[2]
            product_link = self.base_url + link

            quantity_elem = product_elem.select_one("div.col-sm-12.col-xs-7.qnty-selection")
            size = quantity_elem.select_one("span.ng-binding")
            if not size:
                size = quantity_elem.select_one("div:nth-child(1) > span > span:nth-child(1)")
            quantity = size.text

            price_elem = product_elem.select_one("div.po-markup")
            mrp = price_elem.select_one("span.mp-price.ng-scope")
            sp = price_elem.select_one("span.discnt-price").text.replace("MRP: ","").replace("Rs ","")
            if mrp:
                mrp = mrp.text.replace("Rs ","")
            else: 
                mrp = sp
            if "MRP" in mrp:
                a =0

            stock_elem = product_elem.select_one("div.col-xs-12.bskt-opt.ng-scope")
            if "NOTIFY ME" in stock_elem.text:
                stock = "No"
            else:
                stock = "Yes"

            # z = {"Super Category (P0)": super_cat,"Category (P1)": cat,"Sub Category (P2)": sub_cat ,"SKU ID": id,"Image": image,
            # "Brand": brand,"SKU Name": name,"Link": product_link,"SKU Size":quantity,
            # "MRP":mrp,"SP":sp,"Out of Stock?":stock}
            # print(z)
            self.mycsv.writerow({"Super Category (P0)": super_cat,"Category (P1)": cat,"Sub Category (P2)": sub_cat,"SKU ID": id,"Image": image,
            "Brand": brand,"SKU Name": name,"Link": product_link,"SKU Size":quantity,
            "MRP":mrp,"SP":sp,"Out of Stock?":stock})



    def create_csv_file(self):
        """
        create csv
        """
        rowHeaders = ["City","Super Category (P0)","Category (P1)","Sub Category (P2)","SKU ID","Image","Brand","SKU Name","SKU Size","MRP","SP","Link","Active?","Out of Stock?"]
        self.file_csv = open("BB_output.csv", "w", newline="", encoding="utf-8")
        self.mycsv = csv.DictWriter(self.file_csv, fieldnames=rowHeaders)
        self.mycsv.writeheader()

    def tearDown(self):
        self.driver.quit()
        self.file_csv.close()

if __name__ == "__main__":
    # try:
        BBScraper = BBScraper()
        BBScraper.page_load()
        BBScraper.create_csv_file()
        bigbasket_categories = BBScraper.get_category_list()
        for i in range(0,5):
            super_category_p0 = random.choice(list(bigbasket_categories.values()))
            categories_p1 = random.choice(list(super_category_p0.values()))
            for sub_category, link in categories_p1.items():
                BBScraper.page_load(url_tail = link)
                BBScraper.get_product_data_from_list()

        BBScraper.tearDown()
        print('Scraping completed')
    # except Exception as e:
    #     print(e)
    #     print("quitting")
    #     BBScraper.tearDown()