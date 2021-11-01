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

    if (df.isin(temp[['Division', 'Date', 'Time', 'HomeTeam', 'AwayTeam', 'Prediction', 'Pred %']]).all().all()):
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

        towrite.to_excel(writer, sheet_name='HalfTime', index=False)
        temp_temp.to_excel(writer, sheet_name='FullTime', index=False)
        writer.save()
        writer.close()


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
               'Fr Division 2': 'F2'
               }

    print('Downloading schedule..', end='')
    next_match = upcoming('http://www.football-data.co.uk/fixtures.csv')
    print(' ====> Done')

    results_df = pd.DataFrame()

    for key in LEAGUES:
        divis = LEAGUES[key]

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

            result = dixon_coles_simulate_match(params, ht, at)
            res = resultdef(result, ht, at, divis, mdate, mtime)
            results_df = pd.concat([results_df, res])
            print(ht, at, res)

        print(f'\n----- League {divis} completed.. Going to next one -----\n')

    print('Saving Results..', end='')
    save_results_excel(results_df, name)
    print(' ====> Done')