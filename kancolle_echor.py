import time
import requests as req
import json
from threading import Timer as Timer

########################
# user define config
mission = {2:2,3:3,4:5}
api_token = 'f01d18e36e246f00fb437f899ab59a573d367cf7'
api_verno = 1
api_starttime = 1388142501982
host = '125.6.189.135'
baseurl = 'http://'+host
log_file = r'.\log'
api_token_file = r'.\api_token'
connection_retry_time = 10
########################

########################
# config
headers = {
	'Accept': '*/*',
	'Accept-Language': 'zh-CN',
	'Referer': baseurl+'/kcs/port.swf?version=1.5.9', # WARNING!!! version is fixed
	# 'x-flash-version': '11,9,900,170',
	'Content-Type': 'application/x-www-form-urlencoded',
	'Accept-Encoding': 'gzip, deflate',
	'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; WOW64; Trident/6.0),',
	'Host': host,
	# 'DNT': 1,
	'Connection': 'Keep-Alive'
	# 'Pragma': 'no-cache'
}
########################

time_to_sleep = 0
tasks = [] # [[deck_id,back_time,returned]...] sorted
ship_id = {} # {deck_id:[ship_id...]} sorted

def log(tag,role,message):
	print '%s # %s # %s # %s'%(time.ctime(),tag.upper(),role.upper(),message)

def log_to_file(tag,role,message):
	f = open(log_file,'a')
	output = '%s # %s # %s # %s'%(time.ctime(),tag.upper(),role.upper(),message)
	f.write(output+'\n')
	f.close()

############################
# layer3
############################

def getAPItoken():
	f = open(api_token_file,'r')
	result = f.readline()
	f.close()
	if len(result)==40:
		return result
	else:
		return None

def callAPIsub(api,data):
	global api_token
	tmp_api_token = getAPItoken()
	if tmp_api_token is not None:
		api_token = tmp_api_token
	payload = {'api_token':api_token,'api_verno':api_verno}
	payload.update(data)
	url = baseurl+api
	try:
		r = req.post(url,data=payload,headers=headers,timeout=3)
		if r.status_code == 200:
			try:
				json_value = json.loads(r.text.split('=')[1])
				if json_value['api_result'] == 1:
					return json_value
				else:
					log('debug','callAPIsub','api_token expired')
					return None
			except:
				log('debug','callAPIsub','exception caught while parsing json')
				return None
	except:
		log('debug','callAPIsub','exception caught on internet connection')
	return None

def callAPI(api,data):
	for i in range(connection_retry_time):
		result = callAPIsub(api,data)
		if result is not None:
			return result
		else:
			log('info','callAPI','api %s failed, retrying attempt %d'%(api,i))
			time.sleep(3)
	return None

def login_check():
	api = '/kcsapi/api_auth_member/logincheck'
	data = {}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','login_check','login check ok')
		return True
	return False

def deck_port():
	api = '/kcsapi/api_get_member/deck_port'
	data = {}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','deck_port','deck port ok')
		return True
	return False

def ship3():
	api = '/kcsapi/api_get_member/ship3'
	data = {'api_sort_order':2,'api_sort_key':1}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','ship3','ship3 ok')
		return True
	return False

def result_pre():
	f1 = login_check()
	f2 = deck_port()
	f3 = ship3()
	if not (f1 and f2 and f3):
		log('debug','fetch_mission_result','WARNING pre-step not succeed')

############################
# layer2
############################

def start_mission(deck_id,mission_id):
	api = '/kcsapi/api_req_mission/start'
	data = {'api_deck_id':deck_id,'api_mission_id':mission_id}
	jo = callAPI(api,data)
	try:
		backtime = long(jo['api_data']['api_complatetime'])/1000
		log('info','start_mission','fleet %d start mission %d'%(deck_id,mission_id))
		log('info','start_mission','and will return at %s'%(time.ctime(backtime)))
		return backtime
	except:
		log('debug','start_mission','backtime format convert failed')
		return None
	return None

def fetch_mission_result(deck_id):
	api = '/kcsapi/api_req_mission/result'
	data = {'api_deck_id':deck_id}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','fetch_mission_result','mission %s by fleet %d %s'%(jo['api_data']['api_quest_name'],deck_id,jo['api_result_msg']))
		return True
	else:
		log('debug','fetch_mission_result','fetch failed')
		return False

def charge_fleet(deck_id):
	api = '/kcsapi/api_req_hokyu/charge'
	api_id_items = ','.join([str(ele) for ele in ship_id[deck_id]])
	data = {'api_kind':3,'api_id_items':api_id_items}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','charge_fleet','charge fleet %d succeed'%(deck_id))
		# log_to_file('info','charge_fleet',str(jo))
		return True
	else:
		log('debug','charge_fleet','charge fleet %d failed'%(deck_id))
		return False

def fetch_fleet_ship_id(deck_ids):
	api = '/kcsapi/api_get_member/ship2'
	data = {'api_sort_order':2,'api_sort_key':1}
	jo = callAPI(api,data)
	try:
		for id in deck_ids:
			tmp = sorted(jo['api_data_deck'][id-1]['api_ship'])
			ship_id[id] = [ele for ele in tmp if not (ele==-1)]
			if jo['api_data_deck'][id-1]['api_mission'][0]==0:
				charge_fleet(id)
				time.sleep(3)
			else:
				tasks.append([id,jo['api_data_deck'][id-1]['api_mission'][2]/1000,0])
		log('info','fetch_fleet_ship_id','ship_id fetch succeed')
		log_to_file('info','fetch_fleet_ship_id',str(ship_id))
		return True
	except:
		log('debug','fetch_fleet_ship_id','json expected object missing')
		log_to_file('debug','fetch_fleet_ship_id',str(jo))
		return False
	return False

#############################
# layer1
#############################

def init():
	log('info','initializer','kancolle_echor start')
	log('info','initializer','mission setting is '+str(mission))
	for num in mission.keys():
		if not (num in [2,3,4]):
			log('error','initializer','fleet number no in [2,3,4]')
			return False
	
	fetch_fleet_ship_id(mission.keys())
	for m in mission.items():
		if m[0] in [ele[0] for ele in tasks]:
			continue
		time.sleep(3)
		backtime = start_mission(m[0],m[1])
		tasks.append([m[0],backtime,0])
		time.sleep(3)
	tasks.sort(key=lambda ele:ele[1])
	return True

def process():
	log('info','processer','process waked up')
	result_pre()
	for t in tasks:
		if t[1]+10<time.time():
			fetch_mission_result(t[0])
			t[2] = 1
			time.sleep(3)
	for t in tasks:
		if t[2]==1:
			charge_fleet(t[0])
			backtime = start_mission(t[0],mission[t[0]])
			t[1] = backtime
			t[2] = 0
			time.sleep(3)
	tasks.sort(key=lambda ele:ele[1]) # sort tasks
	log('info','processer','sleep to '+time.ctime(12+tasks[0][1]))
	log_to_file('info','processer',str(tasks))
	for t in tasks:
		log_to_file('info','processer','fleet %d return at %s %s'%(t[0],str(t[1]),time.ctime(t[1])))
	global time_to_sleep
	time_to_sleep = 12+tasks[0][1]-time.time()
	schedule()

def schedule():
	global time_to_sleep
	t = Timer(time_to_sleep,process)
	t.start()

def ending():
	log('debug','ending','all process ended')
	return True

def restore_env():
	# global tasks
	# tasks = [[2,1388165773,0],[4,1388166095,0],[3,1388166684,0]]
	global ship_id
	ship_id = {2: [85, 96, 122, 588], 3: [84, 95, 112], 4: [243, 308, 333, 568]}

if __name__ == '__main__':
	# pass
	if init():
		process()
	else:
		ending()
	
	# fetch_fleet_ship_id(mission.keys())

	# fetch_fleet_ship_id([2,3,4])
	# restore_env()
	# charge_fleet(2)
	# # charge_fleet(3)
	# charge_fleet(4)
	
	# start_mission(2,1)
	# start_mission(3,3)
	
	# result_pre()
	# fetch_mission_result(2)
	# time.sleep(5)
	# fetch_mission_result(3)
