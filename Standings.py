import pandas as pd



def Fetch_Data(div='I1'):
    global league_data

    url = f'https://www.football-data.co.uk/mmz4281/2021/{div}.csv'
    league_data = pd.read_csv(url)
    league_data['Date'] = pd.to_datetime(league_data['Date'])
    print(league_data)

def next_matches(div='I1'):
    global fixtures
    global date

    fixtures = pd.read_csv('http://www.football-data.co.uk/fixtures.csv', encoding='cp1252')
    fixtures = fixtures[['Date','Time','Div','HomeTeam','AwayTeam']]
    fixtures = fixtures.loc[fixtures['Div']==div]
    print(fixtures)

    date = fixtures[['Date']].min()
    date = pd.to_datetime(date)
    date = date.values[0]
    print(date)


def make_standing():
    global Standings
    standings = dict()
    for team in league_data['HomeTeam']:
        temp = league_data.loc[league_data['HomeTeam'] == team]['FTR'].value_counts()
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

        Standings[team] = {'Home':
                               {'Win': win,
                                'Draw': draw,
                                'Lose': lose,
                                'Scored':(league_data.loc[league_data['HomeTeam'] == team]['FTHG']).sum(),
                                'Eaten':(league_data.loc[league_data['HomeTeam'] == team]['FTAG']).sum(),
                                'Points': (win * 3) + draw,
                                'Matches': win + draw + lose
                                }
                           }

    for team in league_data['AwayTeam'] :
        temp = league_data.loc[league_data['AwayTeam'] == team]['FTR'].value_counts()
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

        Standings[team].update({'Away':
                               {'Win': win,
                                'Draw': draw,
                                'Lose': lose,
                                'Scored':(league_data.loc[league_data['AwayTeam'] == team]['FTAG']).sum(),
                                'Eaten': (league_data.loc[league_data['AwayTeam'] == team]['FTHG']).sum(),
                                'Points': (win * 3) + draw
                                }
                           })

    for team in Standings.keys():
        Standings[team].update({'Sum':
                                    {
                                    'Win': Standings[team]['Home']['Win']+Standings[team]['Away']['Win'],
                                    'Draw': Standings[team]['Home']['Draw']+Standings[team]['Away']['Draw'],
                                    'Lose': Standings[team]['Home']['Lose']+Standings[team]['Away']['Lose'],
                                    'Scored': Standings[team]['Home']['Scored']+Standings[team]['Away']['Scored'],
                                    'Eaten': Standings[team]['Home']['Eaten'] + Standings[team]['Away']['Eaten'],
                                    'Points': Standings[team]['Home']['Points'] + Standings[team]['Away']['Points']
                                    }
                                })

        standings[team] = { 'Points': Standings[team]['Sum']['Points'],
                            'Motive': '',
                            'Matches': (Standings[team]['Home']['Win'] + Standings[team]['Home']['Draw'] + Standings[team]['Home']['Lose'] +
                                        Standings[team]['Away']['Win'] + Standings[team]['Away']['Draw'] + Standings[team]['Away']['Lose']),
                            'athome_goal_scored': Standings[team]['Home']['Scored'],
                            'athome_goal_against': Standings[team]['Home']['Eaten'],
                            'athome_points': Standings[team]['Home']['Points'],
                            'athome_wins': Standings[team]['Home']['Win'],
                            'athome_draws': Standings[team]['Home']['Draw'],
                            'athome_loses': Standings[team]['Home']['Lose'],
                            'away_goal_scored': Standings[team]['Away']['Scored'],
                            'away_goal_against': Standings[team]['Away']['Eaten'],
                            'away_points': Standings[team]['Away']['Points'],
                            'away_wins': Standings[team]['Away']['Win'],
                            'away_draws': Standings[team]['Away']['Draw'],
                            'away_loses': Standings[team]['Away']['Lose']
                        }

    temp = pd.DataFrame(standings)
    standings_df = temp.transpose()
    standings_df.sort_values(['Points'], inplace=True, ascending=False)
    print(standings_df)
    return(standings_df)


def define_motive(dataframe_standing_table):
    relegation_threshhold = dataframe_standing_table['Points'][-4]
    championsleague_threshhold = dataframe_standing_table['Points'][3]
    europaleague_threshhold = dataframe_standing_table['Points'][5]
    full_schedule = ((dataframe_standing_table.shape[0]-1) *2)


    for temp, row in dataframe_standing_table.iterrows():
        remaining_matches = full_schedule - row['Matches']
        percentage = row['Points'] / row['Matches']
        remaining_points = round(remaining_matches * percentage)
        team_points = row['Points']
        if (
                ((team_points + remaining_points) > relegation_threshhold and team_points < relegation_threshhold+remaining_points) or
                ((team_points + remaining_points) > championsleague_threshhold) or
                ((team_points + remaining_points) > europaleague_threshhold)
        ):
            row['Motive'] = 1
        else:
            row['Motive'] = 0

    print(standings_df)


def prematch_standing(datetokeep):
    pre_standings = dict()
    global prematch_table
    olddata = league_data
    olddata['Date'] = pd.to_datetime(olddata['Date'])
    olddata = olddata.loc[olddata['Date'] <= datetokeep]

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

            prematch_table[team] = {'Home':
                                   {'Win': win,
                                    'Draw': draw,
                                    'Lose': lose,
                                    'Scored': (olddata.loc[olddata['HomeTeam'] == team]['FTHG']).sum(),
                                    'Eaten': (olddata.loc[olddata['HomeTeam'] == team]['FTAG']).sum(),
                                    'Points': (win * 3) + draw
                                    }
                               }

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

            prematch_table[team].update({'Away':
                                        {'Win': win,
                                         'Draw': draw,
                                         'Lose': lose,
                                         'Scored': (olddata.loc[olddata['AwayTeam'] == team]['FTAG']).sum(),
                                         'Eaten': (olddata.loc[olddata['AwayTeam'] == team]['FTHG']).sum(),
                                         'Points': (win * 3) + draw
                                         }
                                    })

    for team in prematch_table.keys():
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

        pre_standings[team] = {'Points': prematch_table[team]['Sum']['Points'],
                           'Motive': '',
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
    pre_standings_df.sort_values(['Points'], inplace=True, ascending=False)
    print(pre_standings_df)
    return (pre_standings_df)

def data_precompile():
    """
    'Team',
    'Point',
    'Motive',
    'athome_goal_scored',
    'athome_goal_against',
    'athome_points',
    'athome_wins',
    'athome_draws',
    'athome_loses',
    'away_goal_scored',
    'away_goal_against',
    'away_points',
    'away_wins',
    'away_draws',
    'away_loses

    """
    for i,row in fixtures.iterrows():
        ht = row['HomeTeam']
        at = row['AwayTeam']

        X1_temp = standings_df[['Points', 'Motive', 'athome_goal_scored', 'athome_goal_against', 'athome_points']].loc[ht]
        X2_temp = standings_df[['Points', 'Motive', 'away_goal_against', 'away_goal_scored', 'away_points']].loc[at]
        X = list(zip(X1_temp, X2_temp))
        print(X)
        y1 = ['GG', 'NG']
        y2 = ['O2.5', 'U2.5']



def nearest(venue, team, date):
    temp = league_data['FTHG'].loc[(league_data[venue] == team) & (league_data['Date'] > date)]
    return (temp.iloc[0])


if __name__ == '__main__':
    league_data = pd.DataFrame()  #our league data from the beginning
    fixtures = pd.DataFrame()     #next league matches (date from the match is used for the prematch_table in order to train our model)
    date = ''                     #next fixture first game

    Standings = {}                #our league standing from the beginning dict of dict of dict
    prematch_table = dict()       #our league standing before a specific date

    Fetch_Data()

    standings_df = make_standing()
    define_motive(standings_df)

    next_matches()
    data_precompile()



    """
    Below only have usage to get stats for a model training
    """
    # input should be a datetime 2020-10-11T00:00:00.000000000 or date year-month-date
    #date = '2020-10-11T00:00:00.000000000'
    #prestandings_df = prematch_standing(date)
    #define_motive(prestandings_df)

