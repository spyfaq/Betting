import pandas as pd
import pickle
import sklearn
from sklearn.preprocessing import StandardScaler
import numpy as np
import matplotlib.pyplot as plt
import os

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

    with open('Standings_italy.data', 'wb') as fil:
        pickle.dump(pre_standings_df, fil)

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
    elif FTR == 'A':
        y1 = 0
    else:
        y1 = 0.5

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

def create_traindataset(data):
    train_data = list()
    for i, row in data.iterrows():

        if i > 2*18 : #meta tn triti agwnistiki
            ht = row['HomeTeam']
            at = row['AwayTeam']
            date = row['Date']

            pre_standings_df = prematch_standing(data, date)
            train_data.append(data_precompile(data, pre_standings_df, ht, at))

    with open('dataset_italy.data', 'wb') as filehandle:
        pickle.dump(train_data, filehandle)

    return (train_data)

def prepare_KNN(dataset, to_pred, stat):
    from sklearn.neighbors import KNeighborsClassifier

    df = pd.concat(dataset, axis=1).transpose()
    scaler = StandardScaler()
    scaler.fit(df.drop(['RESULT', 'O/U', 'GG/NG', 'TEAMS', 'MATCH_DATE', 'SCORE'], axis=1 ))
    scaled_df = scaler.transform(df.drop(['RESULT', 'O/U', 'GG/NG' , 'TEAMS', 'MATCH_DATE', 'SCORE'], axis=1))
    X = pd.DataFrame(scaled_df, columns=df.columns[:-6])
    y = df[stat]
    y = y.astype('int')

    # TRAINING
    x_train, x_test, y_train, y_test = sklearn.model_selection.train_test_split(X, y, test_size=0.1)


    error_rate = []
    for i in range(1, 200):
        knn = KNeighborsClassifier(n_neighbors=i)
        knn.fit(x_train, y_train)
        pred_i = knn.predict(x_test)
        error_rate.append(np.mean(pred_i != y_test))

    plt.figure(figsize=(10, 5))
    plt.plot(range(1, 200), error_rate, color='blue', linestyle='--',
             marker='o', markerfacecolor='red', markersize=10)
    plt.title('Error Rate vs K Value')
    plt.xlabel('K')
    plt.ylabel('Error Rate')
    plt.show()

    # PREDICTION
    df1 = pd.concat(to_pred, axis=1).transpose()
    scaler1 = StandardScaler()
    scaler1.fit(df1.drop(['RESULT', 'O/U', 'GG/NG', 'TEAMS', 'MATCH_DATE', 'SCORE'], axis=1 ))
    scaled_df1 = scaler1.transform(df1.drop(['RESULT', 'O/U', 'GG/NG' , 'TEAMS', 'MATCH_DATE', 'SCORE'], axis=1))
    X_pred = pd.DataFrame(scaled_df1, columns=df1.columns[:-6])

    K = int(input("Give Neighbors: "))
    knn = KNeighborsClassifier(n_neighbors=K)
    knn.fit(X, y)
    pred = knn.predict(X_pred)

    new_label = 'Predicted_KNN' + '_' + stat
    df1[new_label] = pred

    print("1 = GG/O || 0 = NG/U")
    print(df1[['TEAMS',new_label]])

    path = r'D:\Python Apps\Betting\prediction_sklearn'

    if not (os.path.exists(path)):
        os.mkdir(path)

    with open(path+"\_knn.txt", 'a+') as fil:
        np.savetxt(fil, df1[['TEAMS',new_label]].values, fmt='%s')
    fil.close()

def prepare_SVN(dataset, to_pred, stat):
    from sklearn.svm import SVC
    from sklearn.metrics import classification_report, confusion_matrix
    from sklearn.model_selection import GridSearchCV

    df = pd.concat(dataset, axis=1).transpose()
    scaler = StandardScaler()
    scaler.fit(df.drop(['RESULT', 'O/U', 'GG/NG', 'TEAMS', 'MATCH_DATE', 'SCORE'], axis=1))
    scaled_df = scaler.transform(df.drop(['RESULT', 'O/U', 'GG/NG', 'TEAMS', 'MATCH_DATE', 'SCORE'], axis=1))
    X = pd.DataFrame(scaled_df, columns=df.columns[:-6])
    y = df[stat]
    y = y.astype('int')

    x_train, x_test, y_train, y_test = sklearn.model_selection.train_test_split(X, y, test_size=0.1)

    model = SVC()
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    print("1 = GG/O || 0 = NG/U")
    print(confusion_matrix(y_test, predictions))
    print(classification_report(y_test, predictions))

    #optimaze model
    param_grid = {'C': [0.1, 1, 10, 100, 1000, 10000], 'gamma': [1, 0.1, 0.01, 0.001, 0.0001, 0.00001], 'kernel': ['rbf']}
    grid = GridSearchCV(SVC(), param_grid, refit=True, verbose=5)
    grid.fit(X, y)
    print(grid.best_params_)
    print(grid.best_estimator_)

    grid_predictions = grid.predict(x_test)
    print("1 = GG/O || 0 = NG/U")
    print(confusion_matrix(y_test,grid_predictions))
    print(classification_report(y_test, grid_predictions))

    # PREDICTION
    df1 = pd.concat(to_pred, axis=1).transpose()
    scaler1 = StandardScaler()
    scaler1.fit(df1.drop(['RESULT', 'O/U', 'GG/NG', 'TEAMS', 'MATCH_DATE', 'SCORE'], axis=1 ))
    scaled_df1 = scaler1.transform(df1.drop(['RESULT', 'O/U', 'GG/NG' , 'TEAMS', 'MATCH_DATE', 'SCORE'], axis=1))
    X_pred = pd.DataFrame(scaled_df1, columns=df1.columns[:-6])

    pred = grid.predict(X_pred)

    new_label = 'Predicted_SVM' + '_' + stat
    df1[new_label] = pred

    print("1 = GG/O || 0 = NG/U")
    print(df1[['TEAMS', new_label]])

    path = r'D:\Python Apps\Betting\prediction_sklearn'

    if not (os.path.exists(path)):
        os.mkdir(path)

    with open(path+"\_svm.txt", 'a+') as fil:
        np.savetxt(fil, df1[['TEAMS', new_label]].values, fmt='%s')
    fil.close()

def prepare_KMean(dataset, to_pred, stat):
    from sklearn.cluster import KMeans
    from sklearn.metrics import classification_report, confusion_matrix

    df = pd.concat(dataset, axis=1).transpose()
    scaler = StandardScaler()
    scaler.fit(df.drop(['RESULT', 'O/U', 'GG/NG', 'TEAMS', 'MATCH_DATE', 'SCORE'], axis=1))
    scaled_df = scaler.transform(df.drop(['RESULT', 'O/U', 'GG/NG', 'TEAMS', 'MATCH_DATE', 'SCORE'], axis=1))
    X = pd.DataFrame(scaled_df, columns=df.columns[:-6])
    y = df[stat]
    y = y.astype('int')

    x_train, x_test, y_train, y_test = sklearn.model_selection.train_test_split(X, y, test_size=0.1)

    model = KMeans(n_clusters=2)
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    print("1 = GG/O || 0 = NG/U")
    print(confusion_matrix(y_test, predictions))
    print(classification_report(y_test, predictions))

    # PREDICTION
    df1 = pd.concat(to_pred, axis=1).transpose()
    scaler1 = StandardScaler()
    scaler1.fit(df1.drop(['RESULT', 'O/U', 'GG/NG', 'TEAMS', 'MATCH_DATE', 'SCORE'], axis=1 ))
    scaled_df1 = scaler1.transform(df1.drop(['RESULT', 'O/U', 'GG/NG' , 'TEAMS', 'MATCH_DATE', 'SCORE'], axis=1))
    X_pred = pd.DataFrame(scaled_df1, columns=df1.columns[:-6])

    model = KMeans(n_clusters=2)
    model.fit(X, y)
    predictions = model.predict(X_pred)
    df1['Predicted_KMean'] = predictions
    print("1 = GG/O || 0 = NG/U")
    print(df1[['TEAMS','Predicted_KMean']])

    path = r'D:\Python Apps\Betting\prediction_sklearn'

    if not (os.path.exists(path)):
        os.mkdir(path)

    with open(path+"\_kmean.txt", 'a+') as fil:
        np.savetxt(fil, df1[['TEAMS','Predicted_KMean']].values, fmt='%s')
    fil.close()


def upcoming(uri = "http://www.football-data.co.uk/fixtures.csv"):
    next_match = pd.read_csv(uri, encoding='cp1252')
    next_match = next_match[['Date','Time','Div','HomeTeam','AwayTeam']].loc[next_match['Div']=='I1']
    return (next_match)

def create_dataset_for_prediction(next_m, standings):
    date = next_m['Date'].max()

    pred_data = list()
    for i, row in next_m.iterrows():
        ht = row['HomeTeam']
        at = row['AwayTeam']
        date = row['Date']

        X1_temp = (standings.loc[ht].transpose()).drop(labels='Matches')
        X2_temp = (standings.loc[at].transpose()).drop(labels='Matches')

        eachmatch = pd.concat([X1_temp, X2_temp])

        eachmatch['TEAMS'] = ht + ' - ' + at
        eachmatch['MATCH_DATE'] = date
        eachmatch['SCORE'] = ''
        eachmatch['RESULT'] = ''
        eachmatch['O/U'] = ''
        eachmatch['GG/NG'] = ''
        pred_data.append((eachmatch))

    return (pred_data)

if __name__ == '__main__':
    ## for new with download
    data = Fetch_Data()
    train_data = create_traindataset(data)

    ## for existing already downloaded
    #with open('dataset_italy.data', 'rb') as filehandle:
    #    train_data = pickle.load(filehandle)

    with open('dataset_italy_old_2010-2020_.data', 'rb') as filehandle:
        temp = pickle.load(filehandle)

    for _ in temp:
        train_data.append(_)


    # to make a new prediction
    with open('Standings_italy.data', 'rb') as filehandle:
        standings = pickle.load(filehandle)

    next_matches = upcoming()
    pred_data = create_dataset_for_prediction(next_matches, standings)

    for stat in ['O/U', 'GG/NG']:
        prepare_KNN(train_data, pred_data, stat)
        #prepare_SVN(train_data, pred_data, stat)
        #prepare_KMean(train_data, pred_data, stat)