import os
import subprocess
base_dir="/home/ec2-user/run-scripts"
for file in os.listdir(base_dir):
	if file.endswith(".py"):
		print(os.path.join(base_dir, file))
		subprocess.Popen(["python3", os.path.join(base_dir, file)])