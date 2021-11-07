from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import sys
import pandas as pd


def openpage(page):
    """
    :param page: the link to open
    :return: the opened page driver
    """
    global driver
    driver = webdriver.Chrome(executable_path="D:\Python Apps\other reqs\chromedriver.exe")
    driver.get(page)
    driver.minimize_window()
    return()

def banners():
    sleep(3)
    try:
        driver.find_element_by_xpath(
            '//*[@id="landing-page-modal"]/div/div[1]/button').click()
    except:
        print('(No Banner)')

def login():
    # banner
    i = 0
    while True:
        try:
            driver.find_element_by_xpath(
                '//*[@id="landing-page-modal"]/div/div[2]/div[1]/p[2]/a').click()
            break
        except:
            i+=1
            if i >= 3:
                sys.exit('took to long to load')
            else:
                sleep(5)

    #username field
    fr = driver.find_element_by_xpath('//*[@id="iframe-modal"]/div/iframe')
    driver.switch_to.frame(fr)
    driver.find_element_by_xpath('//*[@id="js-login-form"]/div[1]/div[1]/input').send_keys('spyrospnd')
    driver.find_element_by_xpath('//*[@id="js-login-form"]/div[2]/div[1]/input').send_keys('Sp12^Pa16')
    sleep(1)
    driver.find_element_by_xpath('//*[@id="js-login-button"]').click()
    return ()

def find_match(home, away):
    sleep(1)
    temp = driver.find_element_by_xpath('//div[@class="sb-header__header__actions__search-icon GTM-search"]')
    ActionChains(driver).move_to_element(temp).click().perform()
    search = home +' - '+ away
    sleep(2)
    driver.find_element_by_xpath('//*[@id="search-modal"]/div/div[1]/input').send_keys(search)
    sleep(2)
    driver.find_element_by_xpath('//*[@id="search-modal"]/div/div[2]/div[1]/div[2]/div[1]/div[2]/div').click()
    return()

def find_fulltime_stake():
    sleep(2)
    try:
        driver.find_element_by_xpath('/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[6]/div[1]/div[2]/div[1]/div/button')
        div = 0
    except:
        div = 1

    stake = dict()

    prefix = f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{6+div}]/div[{1+div}]/div[2]/'
    for i in [1, 2, 3]:
        path = prefix + f'div[{i}]/div/button'

        try:
            temp = driver.find_element_by_xpath(path)
        except:
            return ('Match has start')

        temp = temp.get_attribute('aria-label')

        words = temp.split(' ')
        temp_r = words[2]
        temp_s = words[-1][:-1]

        stake[temp_r] = temp_s


    temp = driver.find_element_by_xpath(f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{4+div}]/div[1]/div/ul/li[2]/div/div')
    ActionChains(driver).move_to_element(temp).click().perform()
    sleep(2)

    prefix = f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{6+div}]/div[1]/div[2]/'
    for i in [1,2]:
        path = prefix + f'button[{i}]'
        temp = driver.find_element_by_xpath(path)
        temp = temp.get_attribute('aria-label')

        words = temp.split(' ')
        temp_r = words[2][0] + words[3].replace('.','_')
        temp_s = words[-1][:-1]

        stake[temp_r] = temp_s


    prefix = f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{6+div}]/div[2]/div[2]/'
    for i in [1,2,3,4,5,6]:
        path = prefix + f'button[{i}]'
        temp = driver.find_element_by_xpath(path)
        temp = temp.get_attribute('aria-label')

        words = temp.split(' ')
        temp_r = words[2][0] + words[3].replace('.','_')
        temp_s = words[-1][:-1]

        stake[temp_r] = temp_s

    return(stake)

def find_halftime_stake():
    sleep(2)
    try:
        temp = driver.find_element_by_xpath('/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[4]/div[1]/div/ul/li[4]/div/div')
        div = 0
    except:
        div = 1

    try:
        temp = driver.find_element_by_xpath(f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{4+div}]/div[1]/div/ul/li[4]/div/div')
        ActionChains(driver).move_to_element(temp).click().perform()
    except:
        return ('Match has start')

    sleep(2)
    stake = dict()
    prefix = f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{6+div}]/div[1]/div[2]/'
    for i in [1, 2, 3]:
        path = prefix + f'button[{i}]'
        temp = driver.find_element_by_xpath(path)
        temp = temp.get_attribute('aria-label')

        words = temp.split(' ')
        if i == 1:
            temp_r = '1'
        elif i == 2:
            temp_r = 'X'
        else:
            temp_r = '2'

        temp_s = words[-1][:-1]

        stake[temp_r] = temp_s

    prefix = f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{6+div}]/div[4]/div[2]/'
    for i in [1,2,3,4,5,6]:
        path = prefix + f'button[{i}]'
        temp = driver.find_element_by_xpath(path)
        temp = temp.get_attribute('aria-label')

        words = temp.split(' ')
        temp_r = words[2][0] + words[3].replace('.','_')
        temp_s = words[-1][:-1]

        stake[temp_r] = temp_s

    return(stake)

def get_games():
    path_ex = f"{name}.xlsx"
    matches = pd.read_excel(path_ex, sheet_name='HalfTime', engine='openpyxl')
    matches = matches.loc[matches['Stake'].isnull()]
    return(matches)

if __name__ == "__main__":
    link = "https://www.stoiximan.gr/"
    YEAR = '2122'
    name = fr'Dixon_Predictions_{YEAR}'

    matches = get_games()
    for match in matches.index:
        home = matches['HomeTeam'][match]
        away = matches['AwayTeam'][match]

        openpage(link)
        banners()
        find_match(home, away)
        halftime_stakes = find_halftime_stake()
        driver.close()
        sleep(2)