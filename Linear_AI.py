import pandas as pd
import numpy as np
import sklearn
from sklearn import linear_model
import pickle
import time
from sklearn.neighbors import KNeighborsClassifier

data = pd.read_csv("E0.csv")
data = data[['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', "FTR", "HTHG", "HTAG"]]

# replace letters with numbers for AI
mapping = {'H': 1, 'A': 2, 'D': 3 }
data = data.applymap(lambda s: mapping.get(s) if s in mapping else s)

for hometeam in data["HomeTeam"].unique():

    FTHG = data["FTHG"].loc[data['HomeTeam'] == hometeam]
    FTAG = data["FTAG"].loc[data['HomeTeam'] == hometeam]
    FTR = data["FTR"].loc[data['HomeTeam'] == hometeam]
    HTHG = data["HTHG"].loc[data['HomeTeam'] == hometeam]
    HTAG = data["HTAG"].loc[data['HomeTeam'] == hometeam]

    predictresult = "FTR"
    x = list(zip(FTHG, FTAG, HTHG, HTAG))
    y = list(FTR)

    x_train, x_test, y_train, y_test = sklearn.model_selection.train_test_split(x, y, test_size=0.1)

    ## KN Classification
    model = KNeighborsClassifier(n_neighbors=9)
    model.fit(x_train, y_train)
    acc = model.score(x_test, y_test)
    print(hometeam, acc)

    predicted = model.predict(x_test)
    for s in range(len(predicted)):
        print("KN Predicted: ", predicted[s], "data: ", x_test[s], "Actual: ", y_test[s])


    """
## Linear Regrassion
        linear = linear_model.LinearRegression()
        linear.fit(x_train, y_train)
        acc = linear.score(x_test, y_test)

        print ("\n")
        print(hometeam, acc)

        predictions = linear.predict(x_test)
        for s in range (len(predictions)):
            print ("Linear Predicted Outcome: ","{:10.1f}".format(predictions[s]), "data: ", x_test[s], "Actual: ", y_test[s])
"""
    print ("-----------------------------------------------------------------")
