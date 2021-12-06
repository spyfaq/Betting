from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from time import sleep
import sys
import pandas as pd
from datetime import datetime

def openpage(page):
    global driver
    driver = webdriver.Chrome(executable_path="D:\Python Apps\other reqs\chromedriver.exe")
    driver.get(page)
    #driver.minimize_window()
    return()

def banners():
    sleep(3)
    try:
        driver.find_element(By.XPATH,'//*[@id="landing-page-modal"]/div/div[1]/button').click()
    except:
        print('-No Banner-')

def login():
    # banner
    i = 0
    while True:
        try:
            driver.find_element(By.XPATH, '//*[@id="landing-page-modal"]/div/div[2]/div[1]/p[2]/a').click()
            break
        except:
            i+=1
            if i >= 3:
                sys.exit('took to long to load')
            else:
                sleep(5)

    #username field
    fr = driver.find_element(By.XPATH,'//*[@id="iframe-modal"]/div/iframe')
    driver.switch_to.frame(fr)
    driver.find_element(By.XPATH,'//*[@id="js-login-form"]/div[1]/div[1]/input').send_keys('spyrospnd')
    driver.find_element(By.XPATH,'//*[@id="js-login-form"]/div[2]/div[1]/input').send_keys('Sp12^Pa16')
    sleep(1)
    driver.find_element(By.XPATH,'//*[@id="js-login-button"]').click()
    return ()

def find_match(home, away):
    sleep(1)
    temp = driver.find_element(By.XPATH,'//div[@class="sb-header__header__actions__search-icon GTM-search"]')
    ActionChains(driver).move_to_element(temp).click().perform()

    search = home + ' - ' + away
    sleep(2)
    driver.find_element(By.XPATH,'//*[@id="search-modal"]/div/div[1]/input').send_keys(search)
    sleep(2)
    try:
        driver.find_element(By.XPATH,'//*[@id="search-modal"]/div/div[2]/div[1]/div[2]/div[1]/div[2]/span')
        return(False)
    except:
        pass

    try:
        driver.find_element(By.XPATH,'//*[@id="search-modal"]/div/div[2]/div[1]/div[2]/div[1]/div[2]/div').click()
        return (True)
    except:
        return (False)

def go_to_over_tab(div):
    temp = driver.find_element(By.XPATH,f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{4+div}]/div[1]/div/ul/li[2]/div/div')
    ActionChains(driver).move_to_element(temp).click().perform()
    sleep(2)

def place_bet(bet):

    sleep(2)
    try:
        driver.find_element(By.XPATH,
                            '/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[6]/div[1]/div[2]/div[1]/div/button')
        div = 0
    except:
        div = 1

    if 'a' in bet:
        go_to_over_tab(div)
        prefix = f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{6 + div}]/div[14]/div[2]/'
        for i in [1, 3, 5]:
            path = prefix + f'button[{i}]'
            temp = driver.find_element(By.XPATH,path)
            temp = temp.get_attribute('aria-label')
            words = temp.split(' ')
            results = 'a' + words[2][0] + words[3].replace('.', '_')
            results_odd = words[-1][:-1]

            if results == bet:
                driver.find_element(By.XPATH, path).click()
                return ([results, results_odd])

    elif 'h' in bet:
        go_to_over_tab(div)
        prefix = f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{6 + div}]/div[13]/div[2]/'
        for i in [1, 3, 5]:
            path = prefix + f'button[{i}]'
            temp = driver.find_element(By.XPATH,path)
            temp = temp.get_attribute('aria-label')
            words = temp.split(' ')
            results = 'h' + words[2][0] + words[3].replace('.', '_')
            results_odd = words[-1][:-1]

            if results == bet:
                driver.find_element(By.XPATH, path).click()
                return ([results, results_odd])

    elif 'O' in bet:
        go_to_over_tab(div)
        prefix = f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{6 + div}]/div[2]/div[2]/'
        for i in [1,2,3,4,5,6]:
            path = prefix + f'button[{i}]'
            temp = driver.find_element(By.XPATH,path)
            temp = temp.get_attribute('aria-label')
            words = temp.split(' ')
            results = words[2][0] + words[3].replace('.','_')
            results_odd = words[-1][:-1]

            if results == bet:
                driver.find_element(By.XPATH, path).click()
                return ([results, results_odd])

        prefix = f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{6 + div}]/div[1]/div[2]/'
        for i in [1, 2]:
            path = prefix + f'button[{i}]'
            temp = driver.find_element(By.XPATH,path)
            temp = temp.get_attribute('aria-label')
            words = temp.split(' ')
            results = words[2][0] + words[3].replace('.', '_')
            results_odd = words[-1][:-1]

            if results == bet:
                driver.find_element(By.XPATH, path).click()
                return ([results, results_odd])

    elif 'GG' in bet:
        main_path = f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{4 + div}]/div[1]/div/ul/li[3]/div/div'
        temp = driver.find_element(By.XPATH, main_path)
        ActionChains(driver).move_to_element(temp).click().perform()
        sleep(2)

        path = f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{6 + div}]/div[1]/div[2]/button[1]'
        driver.find_element(By.XPATH, path).click()

        temp = driver.find_element(By.XPATH,path)
        temp = temp.get_attribute('aria-label')
        words = temp.split(' ')
        results = 'GG'
        results_odd = words[-1][:-1]
        return ([results, results_odd])

    else:
        if '1' in bet:
            path = f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{6 + div}]/div[{1 + div}]/div[2]/div[1]/div/button'
            driver.find_element(By.XPATH, path).click()

            temp = driver.find_element(By.XPATH,path)
            temp = temp.get_attribute('aria-label')
            words = temp.split(' ')
            results = words[2]
            results_odd = words[-1][:-1]
            return ([results,results_odd])

        elif '2' in bet:
            path = f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{6 + div}]/div[{1 + div}]/div[2]/div[2]/div/button'
            driver.find_element(By.XPATH, path).click()

            temp = driver.find_element(By.XPATH, path)
            temp = temp.get_attribute('aria-label')
            words = temp.split(' ')
            results = words[2]
            results_odd = words[-1][:-1]
            return ([results, results_odd])

        elif 'X' in bet:
            path = f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{6 + div}]/div[{1 + div}]/div[2]/div[3]/div/button'
            driver.find_element(By.XPATH, path).click()

            temp = driver.find_element(By.XPATH, path)
            temp = temp.get_attribute('aria-label')
            words = temp.split(' ')
            results = words[2]
            results_odd = words[-1][:-1]
            return ([results, results_odd])

def load_daily_predictions():
    url = f'https://docs.google.com/spreadsheets/d/1EE64POwwmAmjIZ3BuaqfHFeOEWrCwGouTxCN-9ounhA/gviz/tq?tqx=out:csv&sheet=FullTime'
    df = pd.read_csv(url, decimal=".")
    today =  datetime.strftime(datetime.today(), '%d/%m/%Y')
    todays_match = df.loc[(df['Date'] == today) & (df['Odds'] != '-')]
    return (todays_match)


def main():
    tobet = load_daily_predictions()
    stake = round(STAKE / len(tobet),2)
    if stake < 0.1 :
        print(f"Insufficient balance\nStake is too low\n"
              f"Matches:{len(tobet)}, Stake:{stake}")
    else:
        print(f"Betting {stake}x{len(tobet)}={stake*len(tobet)}")

    openpage("https://en.stoiximan.gr/")
    banners()
    #login()

    bets = list()
    for prediction in tobet.index:
        ht = tobet['HomeTeam'][prediction]
        at = tobet['AwayTeam'][prediction]
        point = tobet['Prediction'][prediction]

        if find_match(ht, at):
            bets.append(place_bet(point))

        print(bets)



if __name__ == '__main__':
    STAKE = 10
    main()