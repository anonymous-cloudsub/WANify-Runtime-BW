# WANify_Realtime_BW
WANify_BWA is a tool based on top of iPerf 3.0, which measures the static and real-time bandwidths (BWs) for a cluster. The static bandwidth is pair-wise BW measurement between interacting nodes, whereas real-time/dynamic BW is the actual BW when all the interacting nodes are communicating at the same time.

# Configurations
All configurations related to the tool can be found inside config.cfg. One of the important configurations is the image ID for respective regions, i.e., AWS us-east-1: <image_id>, etc. An easy way to accomplish this for the entire cluster is by copying the image from one region to all other required regions. Each image must contain Python 3.0 and iPerf 3.0. Additional steps can be found in <provider>/setup/README.txt.

# Running the tool
The tool can be run by using the command "python3 src/main.py" from the project home directory.
