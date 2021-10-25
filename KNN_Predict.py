import pandas as pd
import numpy as np
import sklearn
from sklearn import linear_model
import pickle
import time
from sklearn.neighbors import KNeighborsClassifier

start = time.time()

## access data
data = pd.read_csv("E0.csv")
data = data[['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', "FTR", "HTHG", "HTAG"]]

# replace letters with numbers for AI
mapping = {'H': 1, 'A': 2, 'D': 3 }
data = data.applymap(lambda s: mapping.get(s) if s in mapping else s)

hometeam = "Chelsea"
awayteam = "Wolves"


T1_FTHG = data["FTHG"].loc[data['HomeTeam'] == hometeam]
T1_FTAG = data["FTAG"].loc[data['HomeTeam'] == hometeam]
T1_HTHG = data["HTHG"].loc[data['HomeTeam'] == hometeam]
T1_HTAG = data["HTAG"].loc[data['HomeTeam'] == hometeam]
T1_FTR = data["FTR"].loc[data['HomeTeam'] == hometeam]

T2_FTHG = data["FTHG"].loc[data['AwayTeam'] == awayteam]
T2_FTAG = data["FTAG"].loc[data['AwayTeam'] == awayteam]
T2_HTHG = data["HTHG"].loc[data['AwayTeam'] == awayteam]
T2_HTAG = data["HTAG"].loc[data['AwayTeam'] == awayteam]
T2_FTR = data["FTR"].loc[data['AwayTeam'] == awayteam]

#morfi lista goal omadas 1, goal omadas 2, ...
x1 = list(zip(T1_FTHG, T2_FTAG, T1_HTHG, T2_HTAG))
x2 = list(zip(T2_FTHG, T1_FTAG, T2_HTHG, T1_HTAG))

# outcome only if y1 = y2
y1 = list(T1_FTR)
y2 = list(T2_FTR)

## load each model
f1 = 'Models/' + hometeam + 'Home_Model.sav'
f2 = 'Models/' + awayteam + 'Away_Model.sav'

loaded_model = pickle.load(open(f1, 'rb'))
result = loaded_model.score(x1, y1)
print (result)

print("\n")
print("Total Time:", time.time()-start)