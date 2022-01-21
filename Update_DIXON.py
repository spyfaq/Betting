import pandas as pd
import matplotlib.pyplot as plt
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def download_league_data(url):
    league_data = pd.read_csv(url)
    league_data = league_data[['Div', 'Date', 'Time', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'HTHG', 'HTAG']]

    return (league_data)

def match_matched(results, divis):
    url = f'https://docs.google.com/spreadsheets/d/1EE64POwwmAmjIZ3BuaqfHFeOEWrCwGouTxCN-9ounhA/gviz/tq?tqx=out:csv&sheet=HalfTime'
    prediction_Half = pd.read_csv(url, decimal=".")
    prediction_Half = prediction_Half.loc[prediction_Half['Division'] == divis]
    prediction_Half['unique'] = prediction_Half['Date'].astype(str) + \
                                prediction_Half['HomeTeam'].astype(str) + prediction_Half['AwayTeam'].astype(str)

    url = f'https://docs.google.com/spreadsheets/d/1EE64POwwmAmjIZ3BuaqfHFeOEWrCwGouTxCN-9ounhA/gviz/tq?tqx=out:csv&sheet=FullTime'
    prediction_Full = pd.read_csv(url, decimal=".")
    prediction_Full = prediction_Full.loc[prediction_Full['Division'] == divis]
    prediction_Full['unique'] = prediction_Full['Date'].astype(str) + \
                                prediction_Full['HomeTeam'].astype(str) + prediction_Full['AwayTeam'].astype(str)

    results['unique'] = results['Date'].astype(str) + results['HomeTeam'].astype(str) + results['AwayTeam'].astype(str)

    results.rename(columns={'HTHG': 'HG', 'HTAG': 'AG'}, inplace=True)
    prediction_Half.drop('HG', axis=1, inplace=True)
    prediction_Half.drop('AG', axis=1, inplace=True)
    final_Half = pd.merge(prediction_Half, results[['unique', 'HG', 'AG']], on=['unique'], how="left")
    final_Half.drop('unique', axis=1, inplace=True)

    results.drop('HG', axis=1, inplace=True)
    results.drop('AG', axis=1, inplace=True)
    results2 = results.rename(columns={'FTHG': 'HG', 'FTAG': 'AG'})
    prediction_Full.drop('HG', axis=1, inplace=True)
    prediction_Full.drop('AG', axis=1, inplace=True)
    final_Full = pd.merge(prediction_Full, results2[['unique', 'HG', 'AG']], on=['unique'], how="left")
    final_Full.drop('unique', axis=1, inplace=True)


    def define(row):
        if pd.isna(row['HG']) or pd.isna(row['AG']):
            return ('')

        if row['Outcome'] == 'TRUE' or row['Outcome'] == 'FALSE':
            return(row['Outcome'])

        if row['Prediction'] == 'O3_5' and int(row['HG'] + row['AG']) > 3.5:
            return('TRUE')
        elif row['Prediction'] == 'O2_5' and int(row['HG'] + row['AG']) > 2.5:
            return('TRUE')
        elif row['Prediction'] == 'O1_5' and int(row['HG'] + row['AG']) > 1.5:
            return('TRUE')
        elif row['Prediction'] == 'O0_5' and int(row['HG'] + row['AG']) > 0.5:
            return('TRUE')
        elif row['Prediction'] == 'U0_5' and int(row['HG'] + row['AG']) < 0.5:
            return('TRUE')
        elif row['Prediction'] == 'U1_5' and int(row['HG'] + row['AG']) < 1.5:
            return('TRUE')
        elif row['Prediction'] == 'U2_5' and int(row['HG'] + row['AG']) < 2.5:
            return('TRUE')
        elif row['Prediction'] == 'U3_5' and int(row['HG'] + row['AG']) < 3.5:
            return('TRUE')
        elif row['Prediction'] == 'GG' and int(row['HG']) > 0.5 and int(row['AG']) > 0.5 :
            return('TRUE')
        elif row['Prediction'] == '1' and int(row['HG']) > int(row['AG']):
            return('TRUE')
        elif row['Prediction'] == '2' and int(row['HG']) < int(row['AG']):
            return('TRUE')
        elif row['Prediction'] == 'X' and int(row['HG']) == int(row['AG']):
            return('TRUE')

        elif row['Prediction'] == 'hO0_5' and int(row['HG']) > 0 :
            return('TRUE')
        elif row['Prediction'] == 'hO1_5' and int(row['HG']) > 1:
            return('TRUE')
        elif row['Prediction'] == 'hO2_5' and int(row['HG']) > 2:
            return('TRUE')

        elif row['Prediction'] == 'aO0_5' and int(row['AG']) > 0 :
            return('TRUE')
        elif row['Prediction'] == 'aO1_5' and int(row['AG']) > 1:
            return('TRUE')
        elif row['Prediction'] == 'aO2_5' and int(row['AG']) > 2:
            return('TRUE')

        else:
            return('FALSE')

    final_Half['Outcome'] = final_Half.apply(lambda x: define(x), axis=1)
    final_Full['Outcome'] = final_Full.apply(lambda x: define(x), axis=1)
    return(final_Half, final_Full)

def update_excel(half, full):
    half['Date'] = pd.to_datetime(half['Date'], format='%d/%m/%Y')
    full['Date'] = pd.to_datetime(full['Date'], format='%d/%m/%Y')
    half.sort_values(by=['Date', 'Time', 'HomeTeam'], inplace=True, ascending=True)
    full.sort_values(by=['Date', 'Time', 'HomeTeam'], inplace=True, ascending=True)
    half['Date'] = half['Date'].dt.strftime('%d/%m/%Y')
    full['Date'] = full['Date'].dt.strftime('%d/%m/%Y')
    full.fillna('', inplace=True)
    half.fillna('', inplace=True)

    full_cor_column = full[['Division', 'Date', 'Time', 'HomeTeam', 'AwayTeam', 'Prediction', 'Prediction %', 'History %', 'Weighted %', 'Odds',
                                    'diff %', 'Outcome', 'HG', 'AG',
                                    'HT_Points', 'HT_Matches', 'HT_athome_goal_scored', 'HT_athome_goal_against',
                                    'HT_athome_points', 'HT_athome_wins', 'HT_athome_draws', 'HT_athome_loses',
                                    'AT_Points', 'AT_Matches', 'AT_away_goal_scored', 'AT_away_goal_against',
                                    'AT_away_points', 'AT_away_wins', 'AT_away_draws', 'AT_away_loses']]

    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    credentials = ServiceAccountCredentials.from_json_keyfile_name('share-betting-f978bc9098c1.json', scopes)
    file = gspread.authorize(credentials)
    sheet = file.open("Betting")
    sheet_full = sheet.worksheet('FullTime')
    sheet_half = sheet.worksheet('HalfTime')

    sheet_full.update('A2', full_cor_column.values.tolist())
    sheet_half.update('A2', half.values.tolist())

def plot_show(data, kind):
    data.drop(data.columns[0], axis=1, inplace=True)
    res = data.div(data.sum(axis=1), axis=0) * 100

    ax = res.plot(title=kind, kind="bar", legend=True, stacked=True, width=0.5, grid=True,
                  figsize=(8, 6))
    ax.legend(loc='best', bbox_to_anchor=(0, 1), ncol=1)
    plt.tight_layout()
    for container in ax.containers:
        ax.bar_label(container, label_type='center', fmt='%.1f')
    plt.show()
    plt.close()


if __name__ == '__main__':
    YEAR = '2122'
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
               'De Bundesliga 2': 'D2',
               'It Serie B': 'I2',
               'Sp Segunda': 'SP2',
               'Fr Division 2': 'F2',
               'En League 1': 'E2',
               }

    results_df_half = pd.DataFrame()
    results_df_full = pd.DataFrame()
    for key in LEAGUES:
        divis = LEAGUES[key]

        print(f'Downloading league ({divis}) data..', end='')
        pre = F"mmz4281/{YEAR}/{divis}.csv"
        prefix = "http://www.football-data.co.uk/"
        path = prefix + pre
        league_data = download_league_data(path)
        print(' ====> Done')

        print(f'Evaluating Predictions for league ({divis}) ..', end='')
        curr_league = league_data.loc[league_data['Div'] == divis]
        result_half, result_full = match_matched(curr_league, divis)
        results_df_half = pd.concat([results_df_half, result_half])
        results_df_full = pd.concat([results_df_full, result_full])
        print(' ====> Done')

    print('Saving Results..', end='')
    update_excel(results_df_half, results_df_full)
    print(' ====> Done')