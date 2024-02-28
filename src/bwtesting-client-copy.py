import iperf3
#from ec2_metadata import ec2_metadata
from multiprocessing import Lock
# Set vars
# Remote iperf server IP
remote_site = '172.31.13.247'
# How long to run iperf3 test in seconds
test_duration = 20

# Set Iperf Client Options
# Run 10 parallel streams on port 5201 for duration w/ reverse
client = iperf3.Client()
client.server_hostname = remote_site
client.zerocopy = True
client.verbose = False
client.reverse=True
client.port = 5000
client.num_streams = 1
client.duration = int(test_duration)
client.bandwidth = 1000000000

# Run iperf3 test
result = client.run()

# extract relevant data
sent_mbps = int(result.sent_Mbps)
received_mbps = int(result.received_Mbps)

lock = Lock()
lock.acquire()
with open("/home/ec2-user/status.txt", "a") as myfile:
	myfile.write(remote_site+"{sent_mbps: "+str(sent_mbps)+",")
	myfile.write("received_mbps: "+str(received_mbps)+"}\n")
lock.release()
