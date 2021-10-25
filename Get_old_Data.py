import pandas as pd
import pickle
import time

def Fetch_Data(div='I1', year='2021'):
    url = f'https://www.football-data.co.uk/mmz4281/{year}/{div}.csv'
    league_data = pd.read_csv(url)
    league_data.replace('NaT','NaN',inplace=True)
    league_data = league_data.dropna()
    try:
        league_data['Date'] = pd.to_datetime(league_data['Date'], format="%d/%m/%Y")
    except ValueError:
        league_data['Date'] = pd.to_datetime(league_data['Date'], format="%d/%m/%y")
    except:
        league_data['Date'] = pd.to_datetime(league_data['Date'])

    league_data.sort_values(['Date'], inplace=True, ascending=True)

    print(league_data)
    return (league_data)

def prematch_standing(league_data, datetokeep):
    pre_standings = dict()
    prematch_table = dict()
    olddata = league_data.loc[league_data['Date'] <= datetokeep]

    for team in olddata['HomeTeam']:
            temp = olddata.loc[olddata['HomeTeam'] == team]['FTR'].value_counts()
            try:
                lose = temp['A']
            except:
                lose = 0

            try:
                win = temp['H']
            except:
                win = 0

            try:
                draw = temp['D']
            except:
                draw = 0

            try:
                prematch_table[team] = {'Home':
                                           {'Win': win,
                                            'Draw': draw,
                                            'Lose': lose,
                                            'Scored': (olddata.loc[olddata['HomeTeam'] == team]['FTHG']).sum(),
                                            'Eaten': (olddata.loc[olddata['HomeTeam'] == team]['FTAG']).sum(),
                                            'Points': (win * 3) + draw
                                            }
                                        }
            except:
                prematch_table[team].update({'Home':
                                               {'Win': win,
                                                'Draw': draw,
                                                'Lose': lose,
                                                'Scored': (olddata.loc[olddata['HomeTeam'] == team]['FTHG']).sum(),
                                                'Eaten': (olddata.loc[olddata['HomeTeam'] == team]['FTAG']).sum(),
                                                'Points': (win * 3) + draw
                                                }
                                             })

    for team in olddata['AwayTeam']:
            temp = olddata.loc[olddata['AwayTeam'] == team]['FTR'].value_counts()
            try:
                lose = temp['H']
            except:
                lose = 0

            try:
                win = temp['A']
            except:
                win = 0

            try:
                draw = temp['D']
            except:
                draw = 0

            try:
                prematch_table[team].update({'Away':
                                                {'Win': win,
                                                 'Draw': draw,
                                                 'Lose': lose,
                                                 'Scored': (olddata.loc[olddata['AwayTeam'] == team]['FTAG']).sum(),
                                                 'Eaten': (olddata.loc[olddata['AwayTeam'] == team]['FTHG']).sum(),
                                                 'Points': (win * 3) + draw
                                                 }
                                            })
            except:
                prematch_table[team] = {'Away':
                                            {'Win': win,
                                             'Draw': draw,
                                             'Lose': lose,
                                             'Scored': (olddata.loc[olddata['AwayTeam'] == team]['FTAG']).sum(),
                                             'Eaten': (olddata.loc[olddata['AwayTeam'] == team]['FTHG']).sum(),
                                             'Points': (win * 3) + draw
                                             }
                                        }

    for team in prematch_table.keys():
        try:
            prematch_table[team].update({'Sum':
                                            {
                                                'Win': prematch_table[team]['Home']['Win'] + prematch_table[team]['Away']['Win'],
                                                'Draw': prematch_table[team]['Home']['Draw'] + prematch_table[team]['Away']['Draw'],
                                                'Lose': prematch_table[team]['Home']['Lose'] + prematch_table[team]['Away']['Lose'],
                                                'Scored': prematch_table[team]['Home']['Scored'] + prematch_table[team]['Away']['Scored'],
                                                'Eaten': prematch_table[team]['Home']['Eaten'] + prematch_table[team]['Away']['Eaten'],
                                                'Points': prematch_table[team]['Home']['Points'] + prematch_table[team]['Away']['Points']
                                            }
                                        })
        except:
            prematch_table[team] = {'Sum':
                                        {
                                            'Win': prematch_table[team]['Home']['Win'] + prematch_table[team]['Away']['Win'],
                                            'Draw': prematch_table[team]['Home']['Draw'] + prematch_table[team]['Away']['Draw'],
                                            'Lose': prematch_table[team]['Home']['Lose'] + prematch_table[team]['Away']['Lose'],
                                            'Scored': prematch_table[team]['Home']['Scored'] + prematch_table[team]['Away']['Scored'],
                                            'Eaten': prematch_table[team]['Home']['Eaten'] + prematch_table[team]['Away']['Eaten'],
                                            'Points': prematch_table[team]['Home']['Points'] + prematch_table[team]['Away']['Points']
                                        }
                                    }

        pre_standings[team] = {'Points': prematch_table[team]['Sum']['Points'],
                               'Matches': (prematch_table[team]['Home']['Win'] + prematch_table[team]['Home']['Draw'] +
                                           prematch_table[team]['Home']['Lose'] +
                                           prematch_table[team]['Away']['Win'] + prematch_table[team]['Away']['Draw'] +
                                           prematch_table[team]['Away']['Lose']),
                               'athome_goal_scored': prematch_table[team]['Home']['Scored'],
                               'athome_goal_against': prematch_table[team]['Home']['Eaten'],
                               'athome_points': prematch_table[team]['Home']['Points'],
                               'athome_wins': prematch_table[team]['Home']['Win'],
                               'athome_draws': prematch_table[team]['Home']['Draw'],
                               'athome_loses': prematch_table[team]['Home']['Lose'],
                               'away_goal_scored': prematch_table[team]['Away']['Scored'],
                               'away_goal_against': prematch_table[team]['Away']['Eaten'],
                               'away_points': prematch_table[team]['Away']['Points'],
                               'away_wins': prematch_table[team]['Away']['Win'],
                               'away_draws': prematch_table[team]['Away']['Draw'],
                               'away_loses': prematch_table[team]['Away']['Lose']
                           }

    temp = pd.DataFrame(pre_standings)
    pre_standings_df = temp.transpose()

    pre_standings_df.replace('NaT', 'NaN', inplace=True)
    pre_standings_df = pre_standings_df.dropna()
    pre_standings_df.sort_values(['Points'], inplace=True, ascending=False)


    return (pre_standings_df)

def data_precompile(league_data, standings_df, ht, at):
    X1_temp = (standings_df.loc[ht].transpose()).drop(labels='Matches')
    X2_temp = (standings_df.loc[at].transpose()).drop(labels='Matches')

    eachmatch = pd.concat([X1_temp,X2_temp])

    FTR  = league_data['FTR'].loc[(league_data['HomeTeam']==ht) & (league_data['AwayTeam']==at)].values[0]
    FTHG = league_data['FTHG'].loc[(league_data['HomeTeam'] == ht) & (league_data['AwayTeam'] == at)].values[0]
    FTAG = league_data['FTAG'].loc[(league_data['HomeTeam'] == ht) & (league_data['AwayTeam'] == at)].values[0]

    if FTR == 'H':
        y1 = 1
    else:
        y1 = 0

    if FTHG + FTAG > 2.5 :
        y2 = 1
    else:
        y2 = 0

    if FTHG > 0 and FTAG > 0:
        y3 = 1
    else:
        y3 = 0

    eachmatch['TEAMS'] = ht + ' - ' + at
    eachmatch['MATCH_DATE'] = league_data['Date'].loc[(league_data['HomeTeam']==ht) & (league_data['AwayTeam']==at)].values[0]
    eachmatch['SCORE'] = str(FTHG) + " - " + str(FTAG)
    eachmatch['RESULT'] = y1
    eachmatch['O/U'] = y2
    eachmatch['GG/NG'] = y3

    return(eachmatch)

def create_traindataset_old(data):
    train_data = list()
    for i, row in data.iterrows():

        if i > 2*18 : #meta tn triti agwnistiki
            ht = row['HomeTeam']
            at = row['AwayTeam']
            date = row['Date']

            pre_standings_df = prematch_standing(data, date)
            train_data.append(data_precompile(data, pre_standings_df, ht, at))

        with open('dataset_italy_old_2000-2010_.data', 'ab+') as filehandle:
            pickle.dump(train_data, filehandle)

    return (train_data)


if __name__ == '__main__':
    # for old history data download

    #2010-2020 done
    #2000-2010 done
    for year in range (1, 10):
        timestart = time.time()
        now = str(10 - year).zfill(2)
        nows = str(11 - year).zfill(2)
        bf = now+nows

        data = Fetch_Data(year=bf)
        create_traindataset_old(data)
        print (f'Year: {bf} took {(time.time()-timestart)} secs')