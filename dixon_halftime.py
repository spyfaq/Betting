import pandas as pd
import numpy as np
import warnings, sys, os, openpyxl
from scipy.stats import poisson
from scipy.optimize import minimize


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


def dixon_coles_simulate_match(params_dict, homeTeam, awayTeam, max_goals=6):
    team_avgs = calc_means(params_dict, homeTeam, awayTeam)
    team_pred = [[poisson.pmf(i, team_avg) for i in range(0, max_goals + 1)] for team_avg in team_avgs]
    output_matrix = np.outer(np.array(team_pred[0]), np.array(team_pred[1]))
    correction_matrix = np.array([[rho_correction(home_goals, away_goals, team_avgs[0],
                                                  team_avgs[1], params_dict['rho']) for away_goals in range(2)]
                                  for home_goals in range(2)])
    output_matrix[:2, :2] = output_matrix[:2, :2] * correction_matrix
    return output_matrix


def solve_parameters_decay(dataset, xi=0.001, debug=False, init_vals=None, options={'disp': True, 'maxiter': 100},
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


def resultdef(result, ht, at, divis, mdata, mtime):
    under3_5 = result[0][0] + result[0][1] + result[0][2] + result[1][2] + result[0][3] + result[1][0] + result[1][1] + \
               result[2][0] + result[2][1] + result[3][0]
    under2_5 = result[0][0] + result[0][1] + result[0][2] + result[1][0] + result[1][1] + result[2][0]
    under1_5 = result[0][0] + result[0][1] + result[1][0]
    under0_5 = result[0][0]
    over3_5 = 1 - under3_5
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
            'O3_5': over3_5,
            'O0_5': over0_5,
            '1': home,
            '2': away,
            'X': draw,
            'GG': gg,
            'U1_5': under1_5,
            'U2_5': under2_5,
            }

    outcome = pd.DataFrame(columns=['Division', 'Date', 'Time', 'HomeTeam', 'AwayTeam', 'Prediction', 'Pred %'])
    for res in dict.keys():
        if dict[res] > 0.7:
            outcome.loc[len(outcome)] = [divis, mdata, mtime, ht, at, res, dict[res].round(2)]

    return (outcome)


def def_league(lg):
    if lg == 1:
        csvl = F"mmz4281/{YEAR}/E0.csv"
        divis = csvl[13:15]
    elif lg == 2:
        csvl = F"mmz4281/{YEAR}/E1.csv"
        divis = csvl[13:15]
    elif lg == 3:
        csvl = F"mmz4281/{YEAR}/D1.csv"
        divis = csvl[13:15]
    elif lg == 4:
        csvl = F"mmz4281/{YEAR}/I1.csv"
        divis = csvl[13:15]
    elif lg == 5:
        csvl = F"mmz4281/{YEAR}/SP1.csv"
        divis = csvl[13:16]
    elif lg == 6:
        csvl = F"mmz4281/{YEAR}/F1.csv"
        divis = csvl[13:15]
    elif lg == 7:
        csvl = F"mmz4281/{YEAR}/N1.csv"
        divis = csvl[13:15]
    elif lg == 8:
        csvl = F"mmz4281/{YEAR}/B1.csv"
        divis = csvl[13:15]
    elif lg == 9:
        csvl = F"mmz4281/{YEAR}/P1.csv"
        divis = csvl[13:15]
    elif lg == 10:
        csvl = F"mmz4281/{YEAR}/G1.csv"
        divis = csvl[13:15]
    elif lg == 11:
        csvl = F"mmz4281/{YEAR}/SC0.csv"
        divis = csvl[13:16]
    else:
        sys.exit("No accepteble league selected..")

    return (csvl, divis)


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

    temp = pd.read_excel(path_ex, sheet_name='HalfTime', engine='openpyxl')
    temp_temp = pd.read_excel(path_ex, sheet_name='FullTime', engine='openpyxl')

    if df.isin(temp[['Division', 'Date', 'Time', 'HomeTeam', 'AwayTeam', 'Prediction', 'Pred %']]).all().all():
        print(' ====> Already Existist ..')
        sys.exit('same dataframe..')
    else:
        towrite = pd.concat([temp,df])

        writer = pd.ExcelWriter(path_ex, engine='openpyxl')
        towrite.to_excel(writer, sheet_name='HalfTime', index=False)
        temp_temp.to_excel(writer, sheet_name='FullTime', index=False)
        writer.save()
        writer.close()


if __name__ == '__main__':
    YEAR = '2122'

    print("----------------------------------------------")
    print("|------------- League Selection -------------|")
    print("|- 1: En PremierLeague | 2: En Championship -|")
    print("|- 3: De Bundesliga ---| 4: It Serie A ------|")
    print("|- 5: Sp LaLiga -------| 6: Fr Championnat --|")
    print("|- 7: Nh Eredivisie ---| 8: Bg JupilerLeague |")
    print("|- 9: Pr Liga I -------| 10: Gr SuperLeague -|")
    print("|- 11: SC PremierLeague| 50: All Available --|")
    print("----------------------------------------------")
    # league = int(input("Select League: "))
    league = 50

    if league == 50:
        ran = range(1, 12)
    else:
        ran = range(league, league + 1)

    print('Downloading schedule..', end='')
    next_match = upcoming('http://www.football-data.co.uk/fixtures.csv')
    max = next_match['Date'].max().replace('/', '')
    min = next_match['Date'].min().replace('/', '')
    print(' ====> Done')

    results_df = pd.DataFrame()

    for i in (ran):
        csv1, divis = def_league(i)
        print(f'Downloading league ({divis}) data..', end='')

        prefix = "http://www.football-data.co.uk/"
        path = prefix + csv1

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

            result = dixon_coles_simulate_match(params, ht, at)
            res = resultdef(result, ht, at, divis, mdate, mtime)
            results_df = pd.concat([results_df, res])
            print(ht, at, res)

        print(f'\n----- League {divis} completed.. Going to next one -----\n')

    print('Saving Results..', end='')
    name = fr'Dixon_Predictions_{YEAR}'
    save_results_excel(results_df, name)
    print(' ====> Done')