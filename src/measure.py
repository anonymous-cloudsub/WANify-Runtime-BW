import boto3
import subprocess
import time
import os
from datetime import datetime
import traceback
import json

def runMonitor(username, all_IPs, ip_To_Region, basePort, privateKeyPath, privateIPEnabled, datasetPath, datasetIndex, instanceType, isDynamic, debugEnabled, statusProgressMsgEnabled):
	BASE_PORT=int(basePort)
	countPortIncrs=0
	outputFilePrefix=""
	if not isDynamic:
		outputFilePrefix="static"
	else:
		outputFilePrefix="dynamic"
	globalCountPortIncrs=countPortIncrs
	all_unique_ip_pairs={}

	ip_reg1_used={}
	ip_reg2_used={}
	all_send_ips=[]
	all_send_ips_dict={}
	ip_filtered_stats=[]
	ip_filtered_stats_dict={}

	proc_restore1 = subprocess.Popen(["rm", "src/bwtesting-client.py"])
	proc_restore1.wait()
	proc_restore2 = subprocess.Popen(["cp", "src/bwtesting-client-copy.py", "src/bwtesting-client.py"])
	proc_restore2.wait()
	prevIP="172.31.13.247"
	for ip in all_IPs:
		countPortIncrs=0
		if not isDynamic:
			all_send_ips_dict = {}
		if not(ip in all_send_ips_dict):
			all_send_ips.append(ip)
			all_send_ips_dict[ip]=1
		if debugEnabled:
			print("####### IP-source is: {}".format(ip))
		for ip2 in all_IPs:
			if ip != ip2 and (not((ip+'#'+ip2) in all_unique_ip_pairs or (ip2+'#'+ip) in all_unique_ip_pairs)) and not(ip in ip_reg1_used) and not(ip2 in ip_reg2_used):
				#print("#########ip1: {} and ip2: {}".format(ip,ip2))
				proc_update = subprocess.Popen(["sed", "-i", "s/"+prevIP+"/"+str(ip)+"/g", "src/bwtesting-client.py"])
				proc_update.wait()
				portToBeUpdatedInFile=BASE_PORT+countPortIncrs
				if countPortIncrs != 0:
					#prevPortVal = portToBeUpdatedInFile - 1
					proc_sb_update=subprocess.Popen(["sed", "-i", "s/"+str(BASE_PORT)+"/"+str(portToBeUpdatedInFile)+"/g", "src/bwtesting-client.py"])
					proc_sb_update.wait()
				if debugEnabled:
					print("############ SENDING CONN REQ: {}:{}".format(ip2,portToBeUpdatedInFile))
				if not isDynamic:
					all_send_ips=[]
					ip_filtered_stats=[]
				updatedFileName="src/bwtesting-client-"+str(globalCountPortIncrs+1)+".py"
				procCpy = subprocess.Popen(["cp","src/bwtesting-client.py", updatedFileName])
				procCpy.wait()
				destHostAddress=username+"@"+ip2+":~/run-scripts/"
				while(True):
					proc = subprocess.Popen(["scp", "-i", privateKeyPath, "-o", "StrictHostKeyChecking=no", "-q", updatedFileName, destHostAddress], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
					out, err = proc.communicate()
					if not err:
						if debugEnabled:
							print('No error.\n', out.decode())
						break
					else:
						if debugEnabled:
							print('Will retry! Error!!!\n', err.decode())
				countPortIncrs+=1
				subprocess.Popen(["rm", updatedFileName])
				globalCountPortIncrs+=1
				if not isDynamic:
					all_send_ips.append(ip)
					all_send_ips.append(ip2)
				else:
					if not(ip2 in all_send_ips_dict):
						all_send_ips.append(ip2)
						all_send_ips_dict[ip2]=1

				# all_unique_ip_pairs[ip+'#'+ip2]=1
				# ip_reg1_used[ip]=1
				# ip_reg2_used[ip2]=1
				if not isDynamic:
					ip_filtered_stats.append(ip2)
				else:
					if not(ip2 in ip_filtered_stats_dict):
						ip_filtered_stats.append(ip2)
						ip_filtered_stats_dict[ip2]=1
				proc_restore1 = subprocess.Popen(["rm", "src/bwtesting-client.py"])
				proc_restore1.wait()
				proc_restore2 = subprocess.Popen(["cp", "src/bwtesting-client-copy.py", "src/bwtesting-client.py"])
				proc_restore2.wait()
				if debugEnabled:
					print("isDynamic is {} and globalCountPortIncrs is {} with termination condition for dynamic monitoring at {}".format(isDynamic, globalCountPortIncrs, (len(all_IPs)*len(all_IPs) - len(all_IPs))))
				if not isDynamic or (isDynamic and globalCountPortIncrs == (len(all_IPs)*len(all_IPs) - len(all_IPs))):
					# Sending start.txt to initiate the bandwidth measurement process
					for ip_st in all_send_ips:
						destHostAddress=username+"@"+ip_st+":~/"
						subprocess.Popen(["scp", "-i", privateKeyPath, "-o", "StrictHostKeyChecking=no", "-q", "src/template/start.txt", destHostAddress])

					time.sleep(30)
					if statusProgressMsgEnabled and not isDynamic:
						print("Static monitoring in progress ...", flush=True)
					elif statusProgressMsgEnabled and isDynamic:
						print("Dynamic monitoring in progress ...", flush=True)
					#Gather stats
					statsDict={}
					resultList = []
					try:
						for ip_f in ip_filtered_stats:
							# if debugEnabled:
							# 	print("The source IP for status collection is: {}".format(ip_f))
							destHostAddress=username+"@"+ip_f+":~/status.txt"
							proc = subprocess.Popen(["scp", "-i", privateKeyPath, "-o", "", "-q", destHostAddress, datasetPath])
							proc.wait()

							if(proc.returncode != 0):
								raise Exception("Some ERROR occurred while fetching bandwidth information from instances!")

							FILE_TO_READ=datasetPath+"/status.txt"
		
							with open(FILE_TO_READ, 'r') as f:
								for line in f:
									if(len(line)>1):
										statsDict={}
										
										# if debugEnabled:
										# 	print("Obtained line as: \n {}".format(line))
										statsDict["src"]=ip_f
										splitStr = line.split("{")
										statsDict["dest"]=splitStr[0]
										statsDict["srcRegion"]=ip_To_Region[ip_f]
										statsDict["destRegion"]=ip_To_Region[statsDict["dest"]]
										statsDict["machineType"]=instanceType
										bwValuesSplit = splitStr[1].split(",")
										bwValueSent = int(bwValuesSplit[0].split(":")[1].strip())
										bwValueReceived = int(bwValuesSplit[1].split(":")[1].split("}")[0].strip())
										statsDict["sent_mbps"]=str(bwValueSent)
										statsDict["received_mbps"]=str(bwValueReceived)
										resultList.append(statsDict)
										# if debugEnabled:
										# 	print("Information collected in dictionary is: \n {}".format(statsDict))
										# 	print("Information collected in result list is: \n {}".format(resultList))

							proc = subprocess.Popen(["rm", "-f", datasetPath+"/status.txt"])
							proc.wait()

						outputFileName = datasetPath+"/"+outputFilePrefix+str(datasetIndex)+".json"
						isExistFile = os.path.exists(outputFileName)
						if not isExistFile:
							if debugEnabled:
								print("Output file does not exist. Hence, creating new json file!!!")
							with open(outputFileName, "w") as sampleFile:
								statsDictNew = {}
								statsDictNew["readings"] = resultList
								json.dump(statsDictNew, sampleFile, indent = 4)
						else:
							# if debugEnabled:
							# 	print("Output file exists, therefore SKIPPING file creation!")
							# 	print("Result list to be dumped is: \n {}".format(resultList))
							with open(outputFileName,'r+') as sampleFile:
								fileContents = json.load(sampleFile)
								fileContents["readings"].extend(resultList)
								sampleFile.seek(0)
								json.dump(fileContents, sampleFile, indent = 4)

						# Calling cleanup on associated instances
						for ip_c in all_send_ips:
							destHostAddress=username+"@"+ip_c
							subprocess.Popen(["ssh", "-i", privateKeyPath, "-o", "StrictHostKeyChecking=no", destHostAddress, "sh cleanup.sh"])

					except Exception as e:
						# Calling cleanup on associated instances
						for ip_c in all_send_ips:
							destHostAddress=username+"@"+ip_c
							subprocess.Popen(["ssh", "-i", privateKeyPath, "-o", "StrictHostKeyChecking=no", destHostAddress, "sh cleanup.sh"])

						print("An ERROR occurred while collecting bandwidth information from instances and saving into file!!!")
						print("Exception details: ", e)
						traceback.print_exc()

						subprocess.Popen(["rm", "src/bwtesting-client.py"])
						subprocess.Popen(["cp", "src/bwtesting-client-copy.py", "src/bwtesting-client.py"])
						return -1

	subprocess.Popen(["rm", "src/bwtesting-client.py"])
	subprocess.Popen(["cp", "src/bwtesting-client-copy.py", "src/bwtesting-client.py"])
