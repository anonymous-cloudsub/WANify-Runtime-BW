import tensorflow as tf
from keras.layers import Dense, Conv2D, Flatten, MaxPooling2D, Input, Reshape
import json
import numpy as np
from os.path import exists
import pickle
import os
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

if ACT_DATACENTERS > NUM_DATACENTERS:
	raise Exception("ACT_DATACENTERS cannot be greater than NUM_DATACENTERS. Please re-configure.")

if ACT_DATACENTERS == NUM_DATACENTERS:
	refactor_matrix = np.ones((NUM_DATACENTERS, NUM_DATACENTERS))
	with open(cnnOutputPathAbs + '/refactor.pkl', 'wb') as file:  
		pickle.dump(refactor_matrix, file)
else:
	datasetDirForRefactor = 'test_datasets/genRef'
	if config.has_option('PLUGIN_CONFIGS', 'datasetPathForRefactor'):
		datasetDirForRefactor = config.get('PLUGIN_CONFIGS', 'datasetPathForRefactor')
		datasetDirForRefactor = os.path.abspath(datasetDirForRefactor)

	NUM_SAMPLES = 0
	for file_name in os.listdir(datasetDirForRefactor):
		if(file_name.endswith('json')):
			NUM_SAMPLES = NUM_SAMPLES + 1
	print("NUM_SAMPLES in {} determined is {} !".format(datasetDirForRefactor, NUM_SAMPLES))
	if NUM_DATACENTERS != ACT_DATACENTERS and not(NUM_SAMPLES > 0):
		raise Exception("There are no monitored BWs for {} DCs in {}. Please re-run monitoring by changing configs to ensure at least 1 sample (both static and dynamic) of monitored BWs exist. Or use ACT_DATACENTERS = NUM_DATACENTERS for predicting runtime BWs for {} DCs".format(ACT_DATACENTERS, datasetDirForRefactor, NUM_DATACENTERS))

	readIndex = 1
	NUM_SAMPLES_CPY = NUM_SAMPLES
	# train_x = np.zeros((NUM_SAMPLES, NUM_DATACENTERS, NUM_DATACENTERS))
	# train_y = np.zeros((NUM_SAMPLES, NUM_DATACENTERS, NUM_DATACENTERS))
	prevImprDeterminations = 9999999

	while(NUM_SAMPLES_CPY>0):
		if (not exists(datasetDirForRefactor + '/static'+str(readIndex)+'.json')) or (not exists(datasetDirForRefactor + '/dynamic'+str(readIndex)+'.json')):
			raise Exception("Invalid dataset file for readIndex:{}! Please check if sample files are continuous.".format(readIndex))

		train_x_i=np.zeros((NUM_DATACENTERS, NUM_DATACENTERS))
		train_y_i=np.zeros((NUM_DATACENTERS, NUM_DATACENTERS))
		refactor_matrix = np.ones((NUM_DATACENTERS, NUM_DATACENTERS))
		improvementDeterminations = 0

		# print("Train x")
		# print(train_x_i)
		
		file = open(datasetDirForRefactor + '/static'+str(readIndex)+'.json')
		data = json.load(file)
		for i in data['readings']:
			train_x_i[dcToIndexMap[i["srcRegion"]]][dcToIndexMap[i["destRegion"]]] = int(i["sent_mbps"]) + int(i["received_mbps"])
		# print(train_x_i)
		y_predict_i=model.predict(train_x_i.reshape(1, NUM_DATACENTERS, NUM_DATACENTERS))
		file.close()
		# print(train_x_i)
		# print(y_predict_i[0])

		file = open(datasetDirForRefactor + '/dynamic'+str(readIndex)+'.json')
		data = json.load(file)
		for i in data['readings']:
			train_y_i[dcToIndexMap[i["srcRegion"]]][dcToIndexMap[i["destRegion"]]] = int(i["sent_mbps"]) + int(i["received_mbps"])
		#train_y[readIndex-1]=train_y_i
		file.close()
		#print(train_y[0])
		NUM_SAMPLES_CPY -= 1
		readIndex += 1
		# print("Printing final vals:")
		# print(y_predict_i[0])
		# print("===")
		# print(train_y_i)
		for i in range(NUM_DATACENTERS):
			for j in range(NUM_DATACENTERS):
				if abs(y_predict_i[0][i][j] - train_y_i[i][j]) > 30 and y_predict_i[0][i][j] > 1:
					refactor_matrix[i][j] = float(train_y_i[i][j])/y_predict_i[0][i][j]
		
		# print("The refactor_matrix is:")
		# print(refactor_matrix)

		newReadIndex = (readIndex)%(NUM_SAMPLES)
		improvementDeterminations = 0
		for m in range(NUM_SAMPLES - 1):
			if newReadIndex == 0:
				newReadIndex = NUM_SAMPLES
			train_x_i_2=np.zeros((NUM_DATACENTERS, NUM_DATACENTERS))
			train_y_i_2=np.zeros((NUM_DATACENTERS, NUM_DATACENTERS))
			print("readIndex={} and newReadIndex={}".format(readIndex, newReadIndex))
			file = open(datasetDirForRefactor + '/static'+str(newReadIndex)+'.json')
			data = json.load(file)
			for i in data['readings']:
				train_x_i_2[dcToIndexMap[i["srcRegion"]]][dcToIndexMap[i["destRegion"]]] = int(i["sent_mbps"]) + int(i["received_mbps"])
			# print(train_x_i)
			y_predict_i_2=model.predict(train_x_i_2.reshape(1, NUM_DATACENTERS, NUM_DATACENTERS))
			file.close()

			file = open(datasetDirForRefactor + '/dynamic'+str(newReadIndex)+'.json')
			data = json.load(file)
			for i in data['readings']:
				train_y_i_2[dcToIndexMap[i["srcRegion"]]][dcToIndexMap[i["destRegion"]]] = int(i["sent_mbps"]) + int(i["received_mbps"])
			#train_y[readIndex-1]=train_y_i
			file.close()
		
			for i in range(NUM_DATACENTERS):
				for j in range(NUM_DATACENTERS):
					y_predict_i_2[0][i][j] = y_predict_i_2[0][i][j] * refactor_matrix[i][j]
					if(y_predict_i_2[0][i][j] < 10):
						y_predict_i_2[0][i][j] = train_x_i_2[i][j]

			for i in range(NUM_DATACENTERS):
				for j in range(NUM_DATACENTERS):
					diff = abs(y_predict_i_2[0][i][j] - train_y_i_2[i][j])

					if diff >= 30 and y_predict_i_2[0][i][j] > 1 and train_y_i_2[i][j] > 1:
						improvementDeterminations = improvementDeterminations + diff
			newReadIndex = (newReadIndex+1)%(NUM_SAMPLES)
		print("One test cycle completed!")
		print("improvementDeterminations={} and prevImprDeterminations={}".format(improvementDeterminations, prevImprDeterminations))
		if improvementDeterminations < prevImprDeterminations:
			prevImprDeterminations = improvementDeterminations
			with open(cnnOutputPathAbs + '/refactor.pkl', 'wb') as file:  
				pickle.dump(refactor_matrix, file)

print("Refactor Matrix is created!")
