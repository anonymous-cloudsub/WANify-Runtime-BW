# WANify_Realtime_BW
WANify_BWA is a tool based on top of iPerf 3.0, which measures the static and real-time bandwidths (BWs) for a cluster. The static bandwidth is independently measured pair-wise BWs between the interacting nodes, whereas real-time/dynamic BW is the actual pari-wise BWs when all the interacting nodes are communicating with each other at the same time. The tool can generate newer static/dynamic datasets and train/re-train a Convolutional Neural Network (CNN), which predicts runtime BWs for a given combination of static BWs. Moreover, the tool supports periodic monitoring, that is, it can be configured to collect static/dynamic datasets at fixed intervals. The goal of this tool is to help Geo-distributed Data Analytics (GDA) applications in determining actual runtime BWs for network-aware policies.

# Configurations
All configurations related to the tool can be found inside config.cfg. One of the important configurations is the image ID for respective regions, i.e., AWS us-east-1: <image_id>, etc. An easy way to accomplish this for the entire cluster is by copying the image from one region to all other required regions. Each image must contain Python 3.0 and iPerf 3.0. Additional steps can be found in <provider>/setup/README.txt.

# BW Monitoring and Model Generation
The tool can be run by using the command "python3 src/main.py" from the project's home directory. Note that re-generation of the model might be required when TensorFlow libraries are different between the generated model and user's workspace. Set both 'buildModel' and 'cnnTrainModeOnly' keys to 'True' and run the following command in that case.

```python3 src/main.py```

# Generating refactor matrix
A "refactor matrix" is required when the number of DCs to be used in model prediction is lesser than the number of DCs against which the model was trained. Otherwise, to support generalizability, the refactor matrix consists of all 1s. Irrespective of the scenario under consideration, this command must be run before making any predictions using the generated model.

```python3 src/cnn/genRefactorMatrix.py```

# Predicting real-time BW
In the following command, the second argument denotes the file, which contains statically and independently measured pair-wise bandwidths between the interacting DCs.

```python3 src/cnn/cnnTest.py datasets/static1.json```
