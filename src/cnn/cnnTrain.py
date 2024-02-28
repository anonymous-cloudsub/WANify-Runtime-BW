import tensorflow as tf
from keras.layers import Dense, Conv2D, Flatten, MaxPooling2D, Input, Reshape
import json
import numpy as np
from os.path import exists
import os
import pickle

print("### The tensorflow version is:")
print(tf.__version__)

def createCNNModel(rows, cols):
	input_shape = Input(shape=(rows, cols))

	reshape_layer = tf.keras.layers.Reshape((rows, cols, 1))(input_shape)

	filter_1 = Conv2D(rows, 2, padding="same", activation="relu")(reshape_layer)
	filter_1 = MaxPooling2D((2, 2), strides=(1, 1), padding='same')(filter_1)

	filter_2 = Conv2D(rows, 3, padding="same", activation="relu")(reshape_layer)
	filter_2 = MaxPooling2D((3, 3), strides=(1, 1), padding='same')(filter_2)

	filter_3 = Conv2D(rows, 4, padding="same", activation="relu")(reshape_layer)
	filter_3 = MaxPooling2D((4, 4), strides=(1, 1), padding='same')(filter_3)

	filter_4 = Conv2D(rows, 5, padding="same", activation="relu")(reshape_layer)
	filter_4 = MaxPooling2D((5, 5), strides=(1, 1), padding='same')(filter_4)

	filter_5 = Conv2D(rows, 6, padding="same", activation="relu")(reshape_layer)
	filter_5 = MaxPooling2D((6, 6), strides=(1, 1), padding='same')(filter_5)

	filter_6 = Conv2D(rows, 7, padding="same", activation="relu")(reshape_layer)
	filter_6 = MaxPooling2D((7, 7), strides=(1, 1), padding='same')(filter_6)

	filter_7 = Conv2D(rows, 8, padding="same", activation="relu")(reshape_layer)
	filter_7 = MaxPooling2D((8, 8), strides=(1, 1), padding='same')(filter_7)

	allFilters = tf.keras.layers.concatenate([filter_1, filter_2, filter_3, filter_4, filter_5, filter_6, filter_7], axis=1)
	allFilters = Flatten()(allFilters)

	dense_layer = Dense(256, activation='relu')(allFilters)
	dense_layer2 = Dense(64, activation='relu')(dense_layer)

	output_layer = tf.keras.layers.Reshape((rows, cols))(dense_layer2)
	
	model = tf.keras.Model(input_shape, output_layer)

	optimizer = tf.keras.optimizers.Nadam(0.001)
	model.compile(loss='mae', optimizer=optimizer, metrics=['accuracy','mae'])
	#tf.keras.utils.plot_model(model, to_file='model.svg')
	return model

def startCNNGeneration(NUM_DATACENTERS, datasetPath, cnnPath):
	print("Inside startCNNGeneration method!")

	# NUM_SAMPLES is the total number of static/dynamic samples in the generated dataset. 
	NUM_SAMPLES = 0
	for file_name in os.listdir(datasetPath):
		if(file_name.endswith('json')):
			NUM_SAMPLES = NUM_SAMPLES + 1
	NUM_SAMPLES = NUM_SAMPLES // 2
	print("NUM_SAMPLES determined is {} !".format(NUM_SAMPLES))
	
	model = createCNNModel(NUM_DATACENTERS, NUM_DATACENTERS)
	model.summary()

	#Read train_samples and train_targets
	print("Processing the training dataset!")
	readIndex = 1
	train_x = np.zeros((NUM_SAMPLES, NUM_DATACENTERS, NUM_DATACENTERS))
	train_y = np.zeros((NUM_SAMPLES, NUM_DATACENTERS, NUM_DATACENTERS))

	#Enumerate the IP addresses here
	dcToIndexMap={}
	dcToIndexMap['us-east-1']=0
	dcToIndexMap['us-west-1']=1
	dcToIndexMap['ap-south-1']=2
	dcToIndexMap['ap-southeast-1']=3
	dcToIndexMap['ap-southeast-2']=4
	dcToIndexMap['ap-northeast-1']=5
	dcToIndexMap['eu-west-1']=6
	dcToIndexMap['sa-east-1']=7

	NUM_SAMPLES_CPY = NUM_SAMPLES
	while(NUM_SAMPLES_CPY>0):
		if (not exists(datasetPath + '/static'+str(readIndex)+'.json')) or (not exists(datasetPath + '/dynamic'+str(readIndex)+'.json')):
			raise Exception("Invalid dataset file for readIndex:{}! Please check if sample files are continuous.".format(readIndex))
		
		train_x_i=np.zeros((NUM_DATACENTERS, NUM_DATACENTERS))
		train_y_i=np.zeros((NUM_DATACENTERS, NUM_DATACENTERS))
		
		file = open(datasetPath + '/static'+str(readIndex)+'.json')
		data = json.load(file)
		for i in data['readings']:
			train_x_i[dcToIndexMap[i["srcRegion"]]][dcToIndexMap[i["destRegion"]]] = int(i["sent_mbps"]) + int(i["received_mbps"])
		train_x[readIndex-1]=train_x_i
		file.close()
		#print(train_x[0])

		file = open(datasetPath + '/dynamic'+str(readIndex)+'.json')
		data = json.load(file)
		for i in data['readings']:
			train_y_i[dcToIndexMap[i["srcRegion"]]][dcToIndexMap[i["destRegion"]]] = int(i["sent_mbps"]) + int(i["received_mbps"])
		train_y[readIndex-1]=train_y_i
		file.close()
		#print(train_y[0])
		NUM_SAMPLES_CPY -= 1
		readIndex += 1

	#print(train_x[100])
	#print(train_y[100])
	print("Dataset processing completed!")

	history = model.fit(train_x, train_y, validation_split=0.2, epochs=1000)

	isExistDir = exists(cnnPath)
	if not isExistDir:
		os.makedirs(cnnPath)

	with open(cnnPath + '/model.pkl', 'wb') as file:  
	    pickle.dump(model, file)
	with open(cnnPath + '/history.pkl', 'wb') as file:  
	    pickle.dump(history, file)

