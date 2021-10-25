import pandas as pd
import numpy as np
import sklearn
from sklearn import linear_model
import pickle
import time
from sklearn.neighbors import KNeighborsClassifier

start = time.time()
data = pd.read_csv("E0.csv")
data = data[['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', "FTR", "HTHG", "HTAG"]]

# replace letters with numbers for AI
mapping = {'H': 1, 'A': 2, 'D': 3 }
data = data.applymap(lambda s: mapping.get(s) if s in mapping else s)

for awayteam in data["AwayTeam"].unique():

    FTHG = data["FTHG"].loc[data['AwayTeam'] == awayteam]
    FTAG = data["FTAG"].loc[data['AwayTeam'] == awayteam]
    FTR = data["FTR"].loc[data['AwayTeam'] == awayteam]
    HTHG = data["HTHG"].loc[data['AwayTeam'] == awayteam]
    HTAG = data["HTAG"].loc[data['AwayTeam'] == awayteam]

    predictresult = "FTR"
    x = list(zip(FTHG, FTAG, HTHG, HTAG))
    y = list(FTR)

    x_train, x_test, y_train, y_test = sklearn.model_selection.train_test_split(x, y, test_size=0.1)
    print(x_train.shape)

    ## KN Classification
    model = KNeighborsClassifier(n_neighbors=9)
    model.fit(x_train, y_train)
    acc = model.score(x_test, y_test)
    filename = 'Models/' + awayteam + 'Away_Model.sav'
    pickle.dump(model, open(filename, 'wb'))
    print(awayteam, "Current Acc:", acc)

    predicted = model.predict(x_test)
    for s in range(len(predicted)):
        print("KN Predicted: ", predicted[s], "|- Data: ", x_test[s], "|- Actual: ", y_test[s])


    # training process to keep better accuracy
    best = 0
    for _ in range(1000):
        x_train, x_test, y_train, y_test = sklearn.model_selection.train_test_split(x, y, test_size=0.1)


        model = KNeighborsClassifier(n_neighbors=10)
        model.fit(x_train, y_train)
        acc = model.score(x_test, y_test)

        if acc > best:
            best = acc
            with open(filename, "wb") as f:
                pickle.dump(model, f)

    print(awayteam, "Best Acc: ", best)
    print("-----------------------------------------------------------------")

print("\n")
print("Total Time:", time.time()-start)