import pandas as pd
import sys
import matplotlib.pyplot as plt


def download_league_data():
    prefix = "http://www.football-data.co.uk/"
    pre = F"new/{divis}.csv"

    path = prefix + pre
    league_data = pd.read_csv(path)
    if divis in ['DNK', 'AUT', 'SWZ']:
        season = '20' + YEAR[0:2] + '/20' + YEAR[2:4]
        league_data = league_data.loc[league_data['Season'] == season]

    if divis in ['SWE', 'FIN', 'NOR']:
        season = '20' + YEAR[0:2]
        league_data = league_data.loc[league_data['Season'] == int(season)]

    league_data['Div'] = league_data['Country'].apply(lambda x: LEAGUES[x])
    league_data.rename(columns={'Home': 'HomeTeam', 'Away': 'AwayTeam', 'HG': 'FTHG', 'AG': 'FTAG'},inplace=True)
    league_data = league_data[['Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']]

    return (league_data)

def match_matched(results, divis):
    path_ex = f"{name}.xlsx"

    prediction_Full = pd.read_excel(path_ex, sheet_name='FullTime', engine='openpyxl')
    prediction_Full = prediction_Full.loc[prediction_Full['Division'] == divis]
    prediction_Full['unique'] = prediction_Full['Date'].astype(str) + \
                                prediction_Full['HomeTeam'].astype(str) + prediction_Full['AwayTeam'].astype(str)

    results['unique'] = results['Date'].astype(str) + results['HomeTeam'].astype(str) + results['AwayTeam'].astype(str)

    results2 = results.rename(columns={'FTHG': 'HG', 'FTAG': 'AG'})
    prediction_Full.drop('HG', axis=1, inplace=True)
    prediction_Full.drop('AG', axis=1, inplace=True)
    final_Full = pd.merge(prediction_Full, results2[['unique', 'HG', 'AG']], on=['unique'], how="left")
    final_Full.drop('unique', axis=1, inplace=True)


    def define(row):
        if pd.isna(row['HG']) or pd.isna(row['AG']):
            return ('')

        if row['Outcome'] == '+' or row['Outcome'] == '-':
            return(row['Outcome'])

        if row['Prediction'] == 'O3_5' and int(row['HG'] + row['AG']) > 3.5:
            return('+')
        elif row['Prediction'] == 'O2_5' and int(row['HG'] + row['AG']) > 2.5:
            return('+')
        elif row['Prediction'] == 'O1_5' and int(row['HG'] + row['AG']) > 1.5:
            return('+')
        elif row['Prediction'] == 'O0_5' and int(row['HG'] + row['AG']) > 0.5:
            return('+')
        elif row['Prediction'] == 'U0_5' and int(row['HG'] + row['AG']) < 0.5:
            return('+')
        elif row['Prediction'] == 'U1_5' and int(row['HG'] + row['AG']) < 1.5:
            return ('+')
        elif row['Prediction'] == 'U2_5' and int(row['HG'] + row['AG']) < 2.5:
            return ('+')
        elif row['Prediction'] == 'U3_5' and int(row['HG'] + row['AG']) < 3.5:
            return ('+')
        elif row['Prediction'] == 'GG' and int(row['HG']) > 0.5 and int(row['AG']) > 0.5 :
            return ('+')
        elif row['Prediction'] == '1' and int(row['HG']) > int(row['AG']):
            return ('+')
        elif row['Prediction'] == '2' and int(row['HG']) < int(row['AG']):
            return ('+')
        elif row['Prediction'] == 'X' and int(row['HG']) == int(row['AG']):
            return ('+')
        else:
            return('-')

    final_Full['Outcome'] = final_Full.apply(lambda x: define(x), axis=1)
    return(final_Full)

def update_excel(full):
    path_ex = f"{name}.xlsx"

    writer = pd.ExcelWriter(path_ex, engine='openpyxl')

    full['Date'] = pd.to_datetime(full['Date'], format='%d/%m/%Y')
    full.sort_values(by='Date', inplace=True, ascending=True)
    full['Date'] = full['Date'].dt.strftime('%d/%m/%Y')
    full.to_excel(writer, sheet_name='FullTime', index=False)
    writer.save()
    writer.close()

    full_plot = full.groupby(['Division', 'Outcome']).size().unstack()
    plot_show(full_plot, 'FullTime')

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
    name = fr'Dixon_Predictions_extra_{YEAR}'
    LEAGUES = {
               'Sweden': 'SWE',
               'Austria': 'AUT',
               'Denmark': 'DNK',
               'Norway': 'NOR',
               'Switzerland': 'SWZ',
                'Finland': 'FIN',
               }

    results_df_full = pd.DataFrame()
    for key in LEAGUES:
        divis = LEAGUES[key]


        print(f'Downloading league ({divis}) data..', end='')
        pre = F"mmz4281/{YEAR}/{divis}.csv"
        prefix = "http://www.football-data.co.uk/"
        path = prefix + pre
        league_data = download_league_data()
        print(' ====> Done')

        print(f'Evaluating Predictions for league ({divis}) ..', end='')
        curr_league = league_data.loc[league_data['Div'] == divis]
        result_full = match_matched(curr_league, divis)
        results_df_full = pd.concat([results_df_full, result_full])
        print(' ====> Done')

    print('Saving Results..', end='')
    update_excel(results_df_full)
    print(' ====> Done')