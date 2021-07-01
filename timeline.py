import sys
import time
import pickle
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import mysql.connector
import itertools
from mysql.connector import errorcode
import argparse
from config import *

#Global Variable
driver = None
old_height = 0
firefox_profile_path = "/home/zeryx/.mozilla/firefox/0n8gmjoz.bot"
facebook_https_prefix = "https://"
total_scroll = 5

class SearchUser(object):
    def __init__(self, email, password):
        self.email = accountfacebook.EMAIL
        self.password = accountfacebook.PWD
        global driver

        options = Options()
        # disable notification, audio, and many more
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--mute-audio")
        options.add_argument("--headless")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("no-sandbox")
        try:
            self.driver = webdriver.Chrome(executable_path=configBrowser.driver, options=options)
            driver = self.driver

        except Exception:
            print("Chromedriver not match. Kindly update")
            exit(1)
    
    def login(self, email, password):
        driver = self.driver
        fb_path = facebook_https_prefix + "mbasic.facebook.com"
        driver.get(fb_path)

        #Fill the Login Page
        driver.find_element_by_name("email").send_keys(email)
        driver.find_element_by_name("pass").send_keys(password)

        try:
            driver.find_element_by_id("loginbutton").click()
        except NoSuchElementException:
            try: 
                driver.find_element_by_name("login").click()
            except:
                print("Element login not found.")

        try:
            lainkali_elem = driver.find_element_by_xpath('//a[@href="/login/save-device/cancel/?flow=interstitial_nux&nux_source=regular_login"]')
            lainkali_elem.click()
            time.sleep(1)
        except NoSuchElementException:
            pass       

        #Buat file cookies
        with open('CookiesFb.pkl', 'wb') as filehandler:
            cookies = driver.get_cookies()
            #Nge-casting key expiry dari float ke integer, raiso nek float
            for cookie in cookies:
                if 'expiry' in cookie:
                    cookie['expiry'] = int(cookie['expiry'])
            pickle.dump(cookies, filehandler)

    def get_profil(self):
        global names, note, link, pic
        names = []
        note = []
        link = []
        pic = []
        result=[]
        accounts = driver.find_elements_by_xpath(".//*[@class='bu bv bw']//*[@class='bx']//*[@class='t cd']/a")
        for account in accounts:
            link.append(account.get_attribute("href"))
            notes = account.text.split('\n')
            names.append("" if not notes else notes[0])
            note.append("" if not notes else ' '.join(notes[1:]))
        gambar_cards = driver.find_elements_by_xpath("//*[@class='bu bv bw']//*[@class='bx']//*[@class='n bz']/a/img")
        for image in gambar_cards:
            pic.append(image.get_attribute("src"))

        name2 = []
        for h in names:
            name2.append({'names': h})
        note2 = []
        for i in note:
            note2.append({'notes': i})
        link2 = []
        for j in link:
            link2.append({'links': j})
        pic2 = []
        for k in pic:
            pic2.append({'picture': k})
        
        result = []
        for a1, a2, a3, a4 in zip(name2, note2, link2, pic2):
            result.append({**a1, **a2, **a3, **a4})

        return result

    def scroll(self):
        """Used to do infinity scrolling. Usable on facebook.com. 
        Pretty useless in mbasic.facebook.com."""
        SCROLL_PAUSE_TIME = 2
        current_scrolls = 0

        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            try:
                if current_scrolls == total_scroll:
                    return
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCROLL_PAUSE_TIME)

                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            except TimeoutException:
                break
        return

    def search_people(self, username):
        """Search people by name. """
        savedCookies = pickle.load(open("CookiesFb.pkl", "rb"))
        people_path = facebook_https_prefix + "mbasic.facebook.com/search/people/?q=" + username +"&source=filter&isTrending=0"
        # print(people_path)
        driver.get(people_path)
        time.sleep(1)
        for cookie in savedCookies:
            driver.add_cookie(cookie) 
        driver.get(people_path)
            
    def read_more(self):
        """Click to see more results"""
        delay = WebDriverWait(driver, 5)
        try:
            ReadMore = delay.until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='see_more_pager']//a[.= 'Lihat Hasil Selanjutnya'] ")))
            ReadMore.click()
        except:
            try:
                ReadMore = delay.until(EC.element_to_be_clickable((By.XPATH, ".//div[@id='see_more_pager']//a[.= 'See More Results']"))) 
                ReadMore.click()
            except:
                print("Button See More Results is unavailable. Going to exit. Bye~")
                exit(1)      
            
    def check_cookies(self):
        """Function to 1) load the driver and 2) check if file "CookiesFb.pkl" is exist or not"""
        try:
            driver = self.driver
            my_file = open("CookiesFb.pkl")
            return my_file, driver

        except IOError:
            print("Cookies does not exist. Will create cookies anyway. Wait for a second~")
            #Buka file credential
            self.login(accountfacebook.EMAIL, accountfacebook.PWD)
            print("File cookies created. Next file run will pass login page")

    def init_db(self):    
        mydb = mysql.connector.connect(
                host = configSQL.HOST,
                user= configSQL.USER,
                password= configSQL.PASSWD,
                database= configSQL.DATABASE,
                auth_plugin='mysql_native_password'
            )

        if mydb.is_connected():
            db_info = mydb.get_server_info()
            print("Connected to MySQL Version", db_info)
            print("connection successful")
            
        return mydb.cursor(buffered=True), mydb


def parser_option():
    """Parse Argument. Use argument --help to show the parser option"""
    ap = argparse.ArgumentParser(prog="crawler_fb", 
                                usage="python3 %(prog)s [options]", 
                                description="Crawling Facebook")
    ap.add_argument("-u", "--username",
                    type=str, 
                    help='Input fullname of Facebook you want to crawl. Add double quote for two or more words. e.g: "Hendry Henry Heni", "Joko", "Jennie Blackpink"')
    return ap   

if __name__ == '__main__':
    
    start = datetime.now()

    parser = parser_option()
    args = parser.parse_args()
    SearchUser = SearchUser(accountfacebook.EMAIL,accountfacebook.PWD)  
    SearchUser.check_cookies()
    SearchUser.search_people(args.username)
    result = SearchUser.get_profil()
    sql = "INSERT INTO `facebook` (`url`,`nama`, `keterangan`, `gambar`) VALUES (%(links)s, %(names)s, %(notes)s, %(picture)s )"
    cur, mydb = SearchUser.init_db()
    cur.executemany(sql, result)
    mydb.commit()
    print(cur.rowcount, "record inserted")
    cur.close()

    end = datetime.now()
    time_taken = end - start
    print('Time: ',time_taken)