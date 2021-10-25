import pickle
import pandas as pd

"""
with open('dataset_italy_old_2010-2020.data', 'rb') as filehandle:
    temp = pickle.load(filehandle)

i=0
for _ in temp:
    i +=1
    with open(f'dataset_italy_old_2010-2020_{i}.data', 'wb') as filehandle:
        pickle.dump(_, filehandle)

"""

data = list()
for i in range(1,9):
    with open(f'dataset_italy_old_2010-2020_{i}.data', 'rb') as fl:
        unpickler = pickle.Unpickler(fl)
        # if file is not empty scores will be equal
        # to the value unpickled
        temp = unpickler.load()

    fl.close()

    for _ in temp:
        data.append(_)

with open(f'dataset_italy_old_2010-2020_.data', 'wb') as filehandle:
    pickle.dump(data, filehandle)

print('x')