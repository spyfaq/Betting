import pandas as pd
import sys
import matplotlib.pyplot as plt


def download_league_data(url):
    league_data = pd.read_csv(url)
    league_data = league_data[['Div', 'Date', 'Time', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'HTHG', 'HTAG']]

    return (league_data)

def match_matched(results, divis):
    path_ex = f"{name}.xlsx"
    prediction_Half = pd.read_excel(path_ex, sheet_name='HalfTime', engine='openpyxl')
    prediction_Half = prediction_Half.loc[prediction_Half['Division'] == divis]
    prediction_Half['unique'] = prediction_Half['Date'].astype(str) + \
                                prediction_Half['HomeTeam'].astype(str) + prediction_Half['AwayTeam'].astype(str)

    prediction_Full = pd.read_excel(path_ex, sheet_name='FullTime', engine='openpyxl')
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

    final_Half['Outcome'] = final_Half.apply(lambda x: define(x), axis=1)
    final_Full['Outcome'] = final_Full.apply(lambda x: define(x), axis=1)
    return(final_Half, final_Full)

def update_excel(half, full):
    path_ex = f"{name}.xlsx"

    writer = pd.ExcelWriter(path_ex, engine='openpyxl')

    half['Date'] = pd.to_datetime(half['Date'], format='%d/%m/%Y')
    full['Date'] = pd.to_datetime(full['Date'], format='%d/%m/%Y')
    half.sort_values(by='Date', inplace=True, ascending=True)
    full.sort_values(by='Date', inplace=True, ascending=True)
    half['Date'] = half['Date'].dt.strftime('%d/%m/%Y')
    full['Date'] = full['Date'].dt.strftime('%d/%m/%Y')

    half.to_excel(writer, sheet_name='HalfTime', index=False)
    full.to_excel(writer, sheet_name='FullTime', index=False)
    writer.save()
    writer.close()

    half_plot = half.groupby(['Division', 'Outcome']).size().unstack()
    full_plot = full.groupby(['Division', 'Outcome']).size().unstack()

    plot_show(half_plot, 'HalfTime')
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