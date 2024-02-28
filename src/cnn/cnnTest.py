import tensorflow as tf
from keras.layers import Dense, Conv2D, Flatten, MaxPooling2D, Input, Reshape
import json
import numpy as np
from os.path import exists
import pickle
import os
import sys
import configparser
# import copy

print("### The tensorflow version is:")
print(tf.__version__)

config = configparser.RawConfigParser()
config.read('config.cfg')

if not(config.has_option('PLUGIN_CONFIGS', 'cnnOutputPath')):
	raise Exception("Error: CNN output path is not configured correctly!")
cnnOutputPath = config.get('PLUGIN_CONFIGS', 'cnnOutputPath')
cnnOutputPathAbs = os.path.abspath(cnnOutputPath)

with open(cnnOutputPathAbs + '/model.pkl', 'rb') as file:  
    model = pickle.load(file)

dcToIndexMap={}
dcToIndexMap['us-east-1']=0
dcToIndexMap['us-west-1']=1
dcToIndexMap['ap-south-1']=2
dcToIndexMap['ap-southeast-1']=3
dcToIndexMap['ap-southeast-2']=4
dcToIndexMap['ap-northeast-1']=5
dcToIndexMap['eu-west-1']=6
dcToIndexMap['sa-east-1']=7

NUM_DATACENTERS = 8
if config.has_option('PLUGIN_CONFIGS', 'NUM_DATACENTERS'):
	NUM_DATACENTERS = int(config.get('PLUGIN_CONFIGS', 'NUM_DATACENTERS'))

#ACT_DATACENTERS: Actual number of DCs for runtime BW determination
ACT_DATACENTERS = 8
if config.has_option('PLUGIN_CONFIGS', 'ACT_DATACENTERS'):
	ACT_DATACENTERS = int(config.get('PLUGIN_CONFIGS', 'ACT_DATACENTERS'))

fileToRead = sys.argv[1]

if (not exists(fileToRead)):
	raise Exception("Invalid file for prediction: {}! Check if the file exists.".format(fileToRead))

train_x_i=np.zeros((NUM_DATACENTERS, NUM_DATACENTERS))
train_y_i=np.zeros((NUM_DATACENTERS, NUM_DATACENTERS))
refactor_matrix = np.ones((NUM_DATACENTERS, NUM_DATACENTERS))

file = open(fileToRead)
data = json.load(file)
for i in data['readings']:
	train_x_i[dcToIndexMap[i["srcRegion"]]][dcToIndexMap[i["destRegion"]]] = int(i["sent_mbps"]) + int(i["received_mbps"])

y_predict_i=model.predict(train_x_i.reshape(1, NUM_DATACENTERS, NUM_DATACENTERS))
file.close()
print("The input (static-independent) matrix is: \n{}".format(train_x_i))

if (not exists(cnnOutputPathAbs + '/refactor.pkl')):
	raise Exception("Refactor matrix must exist for {}-DC scenario! Run the genRefactorMatrix.py program.".format(ACT_DATACENTERS))
with open(cnnOutputPathAbs + '/refactor.pkl', 'rb') as file:  
	refactor_matrix = pickle.load(file)
# print("###Refactor matrix is:")
# print(refactor_matrix)
for i in range(NUM_DATACENTERS):
	for j in range(NUM_DATACENTERS):
		y_predict_i[0][i][j] = y_predict_i[0][i][j] * refactor_matrix[i][j]
		if(y_predict_i[0][i][j] < 10):
			y_predict_i[0][i][j] = train_x_i[i][j]

print("The output (real-time) matrix is: \n{}".format(y_predict_i[0]))
