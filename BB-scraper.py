
from bs4 import BeautifulSoup
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import random
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from config.config import email_id


from selenium.webdriver.common.action_chains import ActionChains

class BBScraper():

    def __init__(self):
        self.current_path = os.getcwd()
        self.driver_path = os.path.join(os.getcwd(), 'chromedriver')
        self.driver = webdriver.Chrome(executable_path = self.driver_path)
        self.driver.implicitly_wait(30)
        self.base_url = "https://www.bigbasket.com"
        self.config = os.path.join(os.getcwd(), 'config')
        self.email = email_id

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
        "hover over element"
        hover = ActionChains(self.driver).move_to_element(element)
        hover.perform()

    def get_category_list(self):
        """
        Get list of all coategories and subcategories
        Returns: dict
        """
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
        
        #to scrape data of first 10 products from each 
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

            data = {"Super Category (P0)": super_cat,"Category (P1)": cat,"Sub Category (P2)": sub_cat,"SKU ID": id,"Image": image,
            "Brand": brand,"SKU Name": name,"Link": product_link,"SKU Size":quantity,
            "MRP":mrp,"SP":sp,"Out of Stock?":stock}
            new_row = pd.DataFrame.from_records([data])
            self.df = pd.concat([self.df,new_row])
        
    def create_df(self):
        """
        create df
        """
        headers = ["City","Super Category (P0)","Category (P1)","Sub Category (P2)","SKU ID","Image","Brand","SKU Name","SKU Size","MRP","SP","Link","Active?","Out of Stock?"]
        self.df = pd.DataFrame(columns = headers)

    def tearDown(self):
        self.driver.quit()

    def gsheet(self,df):
        """
        Save data to google sheets
        """
        scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive"]

        credentials = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(self.config,"gs_credentials.json"), scope)
        client = gspread.authorize(credentials)

        file_name = "BigBasket_Data1"
        sheet = client.create(file_name)
        sheet.share(self.email, perm_type='user', role='writer')
        sheet = client.open(file_name).sheet1
        sheet.resize(rows=len(df), cols=len(df.columns))
        sheet.update([df.columns.values.tolist()] + df.values.tolist())

if __name__ == "__main__":
    try:
        BBScraper = BBScraper()
        BBScraper.page_load()
        BBScraper.create_df()
        bigbasket_categories = BBScraper.get_category_list()
        #select 5 random categories
        for i in range(0,5):
            super_category_p0 = random.choice(list(bigbasket_categories.values()))
            categories_p1 = random.choice(list(super_category_p0.values()))
            for sub_category, link in categories_p1.items():
                BBScraper.page_load(url_tail = link)
                BBScraper.get_product_data_from_list()
                
        df = BBScraper.df
        df.fillna("",inplace=True)
        BBScraper.gsheet(df)
        BBScraper.tearDown()
        print('Scraping completed')
    except Exception as e:
        print(e)
        print("quitting")
        BBScraper.tearDown()