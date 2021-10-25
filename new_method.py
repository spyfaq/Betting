import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import  MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense,LSTM

def download_league_data(url):
    league_data = pd.read_csv(url)
    league_data = league_data[['Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'HTHG', 'HTAG', 'Referee', 'HY', 'AY', 'HR', 'AR']]
    return (league_data)

def league_data_results(df):
    def results_o25(row):
        if row['FTHG'] + row['FTAG'] > 2.5:
            return (1)
        else:
            return (0)
    def results_o35(row):
        if row['FTHG'] + row['FTAG'] > 3.5:
            return (1)
        else:
            return (0)
    def results_gg(row):
        if row['FTHG'] > 1 and row['FTAG'] > 1:
            return (1)
        else:
            return (0)
    df['Result_O2.5'] = df.apply(lambda x : results_o25(x), axis=1)
    df['Result_O3.5'] = df.apply(lambda x: results_o35(x), axis=1)
    df['Result_GG'] = df.apply(lambda x: results_gg(x), axis=1)

    def results_ho05(row):
        if row['FTHG'] + row['FTAG'] > 0:
            return (1)
        else:
            return (0)
    def results_ho15(row):
        if row['FTHG'] + row['FTAG'] > 1.5:
            return (1)
        else:
            return (0)
    def results_ho25(row):
        if row['FTHG'] + row['FTAG'] > 2.5:
            return (1)
        else:
            return (0)
    df['Half_Result_O0.5'] = df.apply(lambda x: results_ho05(x), axis=1)
    df['Half_Result_O1.5'] = df.apply(lambda x: results_ho15(x), axis=1)
    df['Half_Result_O2.5'] = df.apply(lambda x: results_ho25(x), axis=1)

    def team_o05(row, x):
        if row[x] > 0:
            return (1)
        else:
            return (0)
    def team_o15(row, x):
        if row[x] > 1.5:
            return (1)
        else:
            return (0)
    def team_o25(row, x):
        if row[x] > 2.5:
            return (1)
        else:
            return (0)
    df['Scored_O.5'] = df.apply(lambda x: team_o05(x,'FTHG'), axis=1)
    df['Scored_1.5'] = df.apply(lambda x: team_o15(x,'FTHG'), axis=1)
    df['Scored_2.5'] = df.apply(lambda x: team_o25(x,'FTHG'), axis=1)

    df['Eaten_O.5'] = df.apply(lambda x: team_o05(x,'FTAG'), axis=1)
    df['Eaten_1.5'] = df.apply(lambda x: team_o15(x,'FTAG'), axis=1)
    df['Eaten_2.5'] = df.apply(lambda x: team_o25(x,'FTAG'), axis=1)

    df['Half_Scored_O.5'] = df.apply(lambda x: team_o05(x, 'HTHG'), axis=1)
    df['Half_Eaten_O.5'] = df.apply(lambda x: team_o05(x, 'HTAG'), axis=1)
    df['Half_Scored_1.5'] = df.apply(lambda x: team_o15(x, 'HTHG'), axis=1)
    df['Half_Eaten_1.5'] = df.apply(lambda x: team_o15(x, 'HTAG'), axis=1)

    def point(row, home, away):
        if row[home] >  row[away]:
            return (3)
        elif row[home] ==  row[away]:
            return (1)
        else:
            return (0)
    df['Home_Point'] = df.apply(lambda x: point(x, 'FTHG', 'FTAG'), axis=1)
    df['Away_Point'] = df.apply(lambda x: point(x, 'FTAG', 'FTHG'), axis=1)

    temp_h = df.groupby('HomeTeam')['Date'].count()
    temp_a = df.groupby('AwayTeam')['Date'].count()

    df = df.merge(temp_h, on='HomeTeam', how='left').rename(columns={'Date_y':'Home_Games'})
    df = df.merge(temp_a, on='AwayTeam', how='left').rename(columns={'Date':'Away_Games', 'Date_x':'Date'})

    global columns
    columns = ['Result_O2.5', 'Result_O3.5', 'Result_GG', 'Half_Result_O0.5', 'Half_Result_O1.5',
               'Scored_O.5', 'Scored_1.5', 'Scored_2.5', 'Eaten_O.5', 'Eaten_1.5', 'Eaten_2.5',
               'Home_Point','Away_Point']


    return(df)

def League_standings(df):
    HT_DATA = df.groupby('HomeTeam')[columns].sum()
    HT_DATA = HT_DATA.merge(df[['HomeTeam','Home_Games']],on='HomeTeam', how='right').drop_duplicates(subset=['HomeTeam'])
    HT_DATA.drop('Away_Point',axis=1,inplace=True)

    AT_DATA = df.groupby('AwayTeam')[columns].sum()
    AT_DATA = AT_DATA.merge(df[['AwayTeam','Away_Games']],on='AwayTeam', how='right').drop_duplicates(subset=['AwayTeam'])
    AT_DATA.drop('Home_Point', axis=1, inplace=True)

    stand = pd.concat([HT_DATA, AT_DATA], axis=1, keys=['Home', 'Away'])
    return(HT_DATA, AT_DATA)

def upcoming(uri):
    next_match = pd.read_csv(uri, encoding='cp1252')
    next_match = next_match[['Date','Time','Div','HomeTeam','AwayTeam']]
    return next_match

def model_prediction(X_train, Y_train):
    model = Sequential()
    model.add(LSTM(64, return_sequences=True, input_shape=(X_train.shape[1], 1)))
    model.add(LSTM(64, return_sequences=False))
    model.add(Dense(32))
    model.add(Dense(32))
    model.add(Dense(1))

    # compile the model
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X_train, Y_train, batch_size=1, epochs=1)

    model.predict()

if __name__ == '__main__':
    data = download_league_data("http://www.football-data.co.uk/mmz4281/2122/E0.csv")
    updated_data = league_data_results(data)
    home, away = League_standings(updated_data)
    next_matches = upcoming('http://www.football-data.co.uk/fixtures.csv')

    scaler = MinMaxScaler(feature_range=(0, 1))

    for match in next_matches.loc[next_matches['Div'] == 'E0'].index:
        ht = next_matches['HomeTeam'][match]
        at = next_matches['AwayTeam'][match]
        dt = next_matches['Date'][match]
        tm = next_matches['Time'][match]
        print(dt, tm, ht, at)

        ht_data = home.loc[home['HomeTeam']==ht]
        at_data = away.loc[away['AwayTeam']==at]
        scaled_home_data = scaler.fit_transform(ht_data.drop(['Home_Point', 'Home_Games', 'HomeTeam'], axis=1))
        scaled_away_data = scaler.fit_transform(at_data.drop(['Away_Point', 'Away_Games', 'AwayTeam'], axis=1))

        model_predictor =