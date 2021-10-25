#!/usr/bin/env python
# coding=utf-8

import time
import os


start = time.time()

if __name__ == "__main__":

    start1 = time.time()
    os.system('Predictions_Safe_new.py')
    print ("Safe executed.. | %s seconds" % (time.time() - start1))

    start1 = time.time()
    os.system('Predictions_FullTime.py')
    print ("Fulltime executed.. | %s seconds" % (time.time() - start1))

    start1 = time.time()
    os.system('Predictions_HalfTime.py')
    print ("HalfTime executed.. | %s seconds" % (time.time() - start1))

    start1 = time.time()
    os.system('Prediction_Update_lastresults.py')
    print ("Results updated.. | %s seconds" % (time.time() - start1))

    start1 = time.time()
    os.system('Prediction_Method_Success.py')
    print ("Methods Updated.. | %s seconds" % (time.time() - start1))


    print("Finished.. --- %s seconds ---" % (time.time() - start))