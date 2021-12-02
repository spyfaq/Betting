import pandas as pd
import numpy as np
import warnings, sys, os, openpyxl
from scipy.stats import poisson
from scipy.optimize import minimize
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import gspread
from oauth2client.service_account import ServiceAccountCredentials

warnings.filterwarnings('ignore')


def calc_means(param_dict, homeTeam, awayTeam):
    return [np.exp(param_dict['attack_' + homeTeam] + param_dict['defence_' + awayTeam] + param_dict['home_adv']),
            np.exp(param_dict['defence_' + homeTeam] + param_dict['attack_' + awayTeam])]


def rho_correction(x, y, lambda_x, mu_y, rho):
    if x == 0 and y == 0:
        return 1 - (lambda_x * mu_y * rho)
    elif x == 0 and y == 1:
        return 1 + (lambda_x * rho)
    elif x == 1 and y == 0:
        return 1 + (mu_y * rho)
    elif x == 1 and y == 1:
        return 1 - rho
    else:
        return 1.0


def dixon_coles_simulate_match(params_dict, homeTeam, awayTeam, max_goals=5):
    team_avgs = calc_means(params_dict, homeTeam, awayTeam)
    team_pred = [[poisson.pmf(i, team_avg) for i in range(0, max_goals + 1)] for team_avg in team_avgs]
    output_matrix = np.outer(np.array(team_pred[0]), np.array(team_pred[1]))
    correction_matrix = np.array([[rho_correction(home_goals, away_goals, team_avgs[0],
                                                  team_avgs[1], params_dict['rho']) for away_goals in range(2)]
                                  for home_goals in range(2)])
    output_matrix[:2, :2] = output_matrix[:2, :2] * correction_matrix
    return output_matrix


def solve_parameters_decay(dataset, xi=0, debug=False, init_vals=None, options={'disp': True, 'maxiter': 100},
                           constraints=[{'type': 'eq', 'fun': lambda x: sum(x[:20]) - 20}], **kwargs):
    teams = np.sort(dataset['HomeTeam'].unique())
    # check for no weirdness in dataset
    away_teams = np.sort(dataset['AwayTeam'].unique())
    if not np.array_equal(teams, away_teams):
        raise ValueError("something not right")
    n_teams = len(teams)
    if init_vals is None:
        # random initialisation of model parameters
        init_vals = np.concatenate((np.random.uniform(0, 1, (n_teams)),  # attack strength
                                    np.random.uniform(0, -1, (n_teams)),  # defence strength
                                    np.array([0, 1.0])  # rho (score correction), gamma (home advantage)
                                    ))

    def dc_log_like_decay(x, y, alpha_x, beta_x, alpha_y, beta_y, rho, gamma, t, xi=xi):
        lambda_x, mu_y = np.exp(alpha_x + beta_y + gamma), np.exp(alpha_y + beta_x)
        return np.exp(-xi * t) * (np.log(rho_correction(x, y, lambda_x, mu_y, rho)) +
                                  np.log(poisson.pmf(x, lambda_x)) + np.log(poisson.pmf(y, mu_y)))

    def estimate_paramters(params):
        score_coefs = dict(zip(teams, params[:n_teams]))
        defend_coefs = dict(zip(teams, params[n_teams:(2 * n_teams)]))
        rho, gamma = params[-2:]
        log_like = [
            dc_log_like_decay(row.HomeGoals, row.AwayGoals, score_coefs[row.HomeTeam], defend_coefs[row.HomeTeam],
                              score_coefs[row.AwayTeam], defend_coefs[row.AwayTeam],
                              rho, gamma, row.time_diff, xi=xi) for row in dataset.itertuples()]
        return -sum(log_like)

    sys.stdout = open(os.devnull, 'w')
    opt_output = minimize(estimate_paramters, init_vals, options=options, constraints=constraints)
    sys.stdout = sys.__stdout__
    if debug:
        # sort of hacky way to investigate the output of the optimisation process
        return opt_output
    else:
        return dict(zip(["attack_" + team for team in teams] +
                        ["defence_" + team for team in teams] +
                        ['rho', 'home_adv'],
                        opt_output.x))


def resultdef(result, ht, at, divis, mdata, mtime, stakes):
    under2_5 = result[0][0] + result[0][1] + result[0][2] + result[1][0] + result[1][1] + result[2][0]
    under1_5 = result[0][0] + result[0][1] + result[1][0]
    under0_5 = result[0][0]
    over2_5 = 1 - under2_5
    over1_5 = 1 - under1_5
    over0_5 = 1 - under0_5

    home = np.sum(np.tril(result, -1))
    away = np.sum(np.triu(result, 1))
    draw = np.sum(np.diag(result))

    temp = np.delete(result, 0, 1)
    goalgoal = np.delete(temp, 0, 0)
    gg = np.sum(goalgoal)

    dict = {'O1_5': over1_5,
            'O2_5': over2_5,
            'O0_5': over0_5,
            '1': home,
            '2': away,
            'X': draw,
            'GG': gg,
            }

    outcome = pd.DataFrame(columns=['Division', 'Date', 'Time', 'HomeTeam', 'AwayTeam', 'Prediction', 'Prediction %', 'History %', 'Weighted %', 'Odds'])
    for res in dict.keys():
        if dict[res] > 0.66:
            hist_dict = historyfunc(path, ht, at)
            try:
                hist_perc = round(hist_dict[res], 2)
                Weighted = (dict[res] * 0.85 + hist_dict[res] * 0.15).round(2)
            except:
                Weighted = '-'
                hist_perc = '-'

            try:
                outcome.loc[len(outcome)] = [divis, mdata, mtime, ht, at, res, dict[res].round(2), hist_perc,  Weighted, stakes[res]]
            except:
                outcome.loc[len(outcome)] = [divis, mdata, mtime, ht, at, res, dict[res].round(2), hist_perc, Weighted, '-']

    return (outcome)


def download_league_data(url):
    league_data = pd.read_csv(url)
    league_data['Date'] = pd.to_datetime(league_data['Date'])
    league_data['time_diff'] = (league_data['Date'].max() - league_data['Date']).dt.days
    league_data = league_data[['HomeTeam', 'AwayTeam', 'HTHG', 'HTAG', 'time_diff']]
    league_data = league_data.rename(columns={'HTHG': 'HomeGoals', 'HTAG': 'AwayGoals'})

    return (league_data)


def upcoming(uri):
    next_match = pd.read_csv(uri, encoding='cp1252')
    next_match = next_match[['Date', 'Time', 'Div', 'HomeTeam', 'AwayTeam']]
    return next_match


def save_results_excel(df, name):
    path_ex = f"{name}.xlsx"

    while True:
        try:
            temp = pd.read_excel(path_ex, sheet_name='HalfTime', engine='openpyxl')
            temp_temp = pd.read_excel(path_ex, sheet_name='FullTime', engine='openpyxl')
            break
        except PermissionError:
            print('File is open.. waiting one minute before trying again.')
            sleep(60)

    if (df.isin(temp[['Division', 'Date', 'Time', 'HomeTeam', 'AwayTeam', 'Prediction', 'Prediction %']]).all().all()):
        print(' ====> Already Existist ..')
        sys.exit('same dataframe..')
    else:
        towrite = pd.concat([temp,df])

        writer = pd.ExcelWriter(path_ex, engine='openpyxl')

        towrite['Date'] = pd.to_datetime(towrite['Date'], format='%d/%m/%Y')
        temp_temp['Date'] = pd.to_datetime(temp_temp['Date'], format='%d/%m/%Y')
        towrite.sort_values(by='Date', inplace=True, ascending=True)
        temp_temp.sort_values(by='Date', inplace=True, ascending=True)
        towrite['Date'] = towrite['Date'].dt.strftime('%d/%m/%Y')
        temp_temp['Date'] = temp_temp['Date'].dt.strftime('%d/%m/%Y')

        while True:
            try:
                towrite.to_excel(writer, sheet_name='HalfTime', index=False)
                temp_temp.to_excel(writer, sheet_name='FullTime', index=False)
                writer.save()
                writer.close()
                break
            except PermissionError:
                print('File is open.. waiting one minute before trying again.')
                sleep(60)

def save_results_online(df, name):
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    credentials = ServiceAccountCredentials.from_json_keyfile_name('share-betting-f978bc9098c1.json', scopes)
    file = gspread.authorize(credentials)
    sheet = file.open("Betting")
    sheet = sheet.worksheet(name)

    rows_count = len(sheet.get_all_values()) + 1
    cell = f'A{rows_count}'

    url = f'https://docs.google.com/spreadsheets/d/1EE64POwwmAmjIZ3BuaqfHFeOEWrCwGouTxCN-9ounhA/gviz/tq?tqx=out:csv&sheet={name}'
    temp = pd.read_csv(url)

    if (df.isin(temp[['Division', 'Date', 'Time', 'HomeTeam', 'AwayTeam']]).all().all()):
        print(' ====> Already Existist ..')
        sys.exit('same dataframe..')
    else:
        df.sort_values(by=['Date', 'Time', 'HomeTeam'], inplace=True, ascending=True)
        sheet.update(cell, df.values.tolist())

def openpage(page):
    """
    :param page: the link to open
    :return: the opened page driver
    """
    global driver
    driver = webdriver.Chrome(executable_path="D:\Python Apps\other reqs\chromedriver.exe")
    driver.get(page)
    #driver.minimize_window()
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


    temp_gg = f'/html/body/div[1]/div/section[2]/div[4]/div[2]/section/div[{6+div}]/div[28]/div[2]/button[1]'
    temp = driver.find_element_by_xpath(temp_gg)
    temp = temp.get_attribute('aria-label')

    words = temp.split(' ')
    temp_r = 'GG'
    temp_s = words[-1][:-1]

    stake[temp_r] = temp_s

    return(stake)

def historyfunc(path, hw, aw):
    """
    :return: history percentage of home win, away win, over, under
    """
    history = list()
    win = 0
    lose = 0
    draw = 0
    ov2_5 = 0
    ov_5 = 0
    ov1_5 = 0
    gg = 0

    for year in range(1, 5):

        now = str(int(YEAR[0:2]) - year)
        nows = str(int(YEAR[2:4]) - year)
        bf = now + nows
        ncsv = path.replace(f"{YEAR}", bf)
        old_data = pd.read_csv(ncsv, encoding='latin1')
        old_data = old_data[['HomeTeam', 'AwayTeam', 'HTHG', 'HTAG']]
        ht_found = old_data.loc[(old_data["HomeTeam"] == hw)]
        try:
            if (ht_found.loc[ht_found["AwayTeam"] == aw]['HTHG'].iloc[0]) > (
            ht_found.loc[ht_found["AwayTeam"] == aw]['HTAG'].iloc[0]):
                win = win + 1
            elif (ht_found.loc[ht_found["AwayTeam"] == aw]['HTHG'].iloc[0]) < (
            ht_found.loc[ht_found["AwayTeam"] == aw]['HTAG'].iloc[0]):
                lose = lose + 1
            elif (ht_found.loc[ht_found["AwayTeam"] == aw]['HTHG'].iloc[0]) == (
            ht_found.loc[ht_found["AwayTeam"] == aw]['HTAG'].iloc[0]):
                draw = draw + 1

            if (ht_found.loc[ht_found["AwayTeam"] == aw]['HTHG'].iloc[0]) + (
            ht_found.loc[ht_found["AwayTeam"] == aw]['HTAG'].iloc[0]) > 2:
                ov2_5 = ov2_5 + 1

            if (ht_found.loc[ht_found["AwayTeam"] == aw]['HTHG'].iloc[0]) + (
            ht_found.loc[ht_found["AwayTeam"] == aw]['HTAG'].iloc[0]) > 2:
                ov1_5 = ov1_5 + 1

            if (ht_found.loc[ht_found["AwayTeam"] == aw]['HTHG'].iloc[0]) + (
            ht_found.loc[ht_found["AwayTeam"] == aw]['HTAG'].iloc[0]) > 1:
                ov_5 = ov_5 + 1

            if ((ht_found.loc[ht_found["AwayTeam"] == aw]['HTHG'].iloc[0]) >1) and (
            ht_found.loc[ht_found["AwayTeam"] == aw]['HTAG'].iloc[0]) > 1:
                gg = gg + 1

        except:
            print(hw, "-", aw, "not played during", bf)

    if win + draw + lose > 0:
        totalm = win + draw + lose
        perc_h = win / totalm
        perc_d = draw / totalm
        perc_a = lose / totalm
        perc_o05 = ov_5 / totalm
        perc_o15 = ov1_5 / totalm
        perc_o25 = ov2_5 / totalm
        perc_gg = gg / totalm
    else:
        perc_h = '-'
        perc_d = '-'
        perc_a = '-'
        perc_o05 = '-'
        perc_o15 = '-'
        perc_o25 = '-'
        perc_gg = '-'
    
    dict = {'O1_5': perc_o15,
            'O2_5': perc_o25,
            'O0_5': perc_o05,
            '1': perc_h,
            '2': perc_a,
            'X': perc_d,
            'GG': perc_gg
            }

    return (dict)

if __name__ == '__main__':
    YEAR = '2122'
    name = fr'Dixon_Predictions_{YEAR}'
    LEAGUES = {'En PremierLeague': 'E0',
               'En Championship': 'E1',
               'De Bundesliga': 'D1',
               'It Serie A': 'I1',
               'Sp LaLiga': 'SP1',
               'Fr Championnat': 'F1',
               'Nh Eredivisie': 'N1',
               'Bg JupilerLeague': 'B1',
               'Pr Liga I': 'P1',
               'Gr SuperLeague': 'G1',
               'SC PremierLeague': 'SC1',
               'De Bundesliga 2': 'D2',
               'It Serie B': 'I2',
               'Sp Segunda': 'SP2',
               'Fr Division 2': 'F2',
               'En League 1': 'E2',
               }

    print('Downloading schedule..', end='')
    next_match = upcoming('http://www.football-data.co.uk/fixtures.csv')
    print(' ====> Done')

    results_df = pd.DataFrame()

    for key in LEAGUES:
        divis = LEAGUES[key]

        if (divis in next_match['Div'].unique()) == False:
            print(f'\n----- No match to simulate for league {divis}.. Going to next one -----\n')
            continue

        print(f'Downloading league ({divis}) data..', end='')
        prefix = "http://www.football-data.co.uk/"
        pre = F"mmz4281/{YEAR}/{divis}.csv"
        path = prefix + pre
        league_data = download_league_data(path)
        print(' ====> Done')

        print(f'Calculating parameters decay for {divis}..', end='')
        params = solve_parameters_decay(league_data)
        print(' ====> Done')

        print(f'Simulating matches for {divis}..')
        for match in next_match.loc[next_match['Div'] == divis].index:
            ht = next_match['HomeTeam'][match]
            at = next_match['AwayTeam'][match]
            mdate = next_match['Date'][match]
            mtime = next_match['Time'][match]


            openpage("https://en.stoiximan.gr/")
            try:
                banners()
                find_match(ht, at)
                halftime_stakes = find_halftime_stake()
            except:
                halftime_stakes = '-'

            driver.close()
            sleep(2)


            result = dixon_coles_simulate_match(params, ht, at)
            res = resultdef(result, ht, at, divis, mdate, mtime, halftime_stakes)
            results_df = pd.concat([results_df, res])
            print(res)

        print(f'\n----- League {divis} completed.. Going to next one -----\n')

    print('Saving Results..', end='')
    #save_results_excel(results_df, name)
    save_results_online(results_df, 'HalfTime')
    print(' ====> Done')