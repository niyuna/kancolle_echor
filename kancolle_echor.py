import time
import requests as req
import json
import sys
from threading import Timer as Timer

########################
# user define config
mission = {2:5,3:2}
api_token = '9e5d38e2717f200285eacee6acffef41e7ac3b3f'
api_verno = 1
host = '125.6.189.135'
log_file = r'log'
api_token_file = r'api_token'
sleep_time_file = r'sleep_time'
counter_file = r'counter'
connection_retry_time = 10
enable_auto_mission = True
enable_auto_battle = True
enable_auto_repair = True
ss_id = [695,93,365,704]
ss_loc = 1 # 0~5
########################

########################
# config
baseurl = 'http://'+host
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

class ship():
	id = -1
	cond = -1
	life = -1
	max_life = -1
	
all_ships = [] # [ship...]
all_ss = ss_id # [ss_ship_id...]
all_fleets = {} # {deck_id:[ship_id...]} sorted # deck_id:1,2,3,4
repair_dock = {} # {dock_id:ship_id} # 0 for empty # ndock_id:1,2,3,4
on_mission = {} # {deck_id:state} # deck_id:1,2,3,4 # state: -1 for not, else the time it returns
tasks = [] # [[deck_id,back_time,returned]...] sorted
midnight_flag = 0 # midnight flag for every battle
battle_cnt = 0
sleep_time = 1800

def log(tag,role,message):
	print '%s # %s # %s # %s'%(time.ctime(),tag.upper(),role.upper(),message)

def log_to_file(tag,role,message):
	f = open(log_file,'a')
	output = '%s # %s # %s # %s'%(time.ctime(),tag.upper(),role.upper(),message)
	f.write(output+'\n')
	f.close()

def write_sleep_time():
	f = open(sleep_time_file,'w')
	f.write(str(int(sleep_time)))
	f.close()

############################
# api call
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
	# tmp_api_token = getAPItoken()
	# if tmp_api_token is not None:
	# 	api_token = tmp_api_token
	payload = {'api_token':api_token,'api_verno':api_verno}
	payload.update(data)
	url = baseurl+api
	try:
		r = req.post(url,data=payload,headers=headers,timeout=15)
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
	log('info','callAPI','reach max limit, restart system in 60s')
	global sleep_time
	sleep_time = 60
	write_sleep_time()
	sys.exit(0)
	return None

def parse_ship(jo):
	global all_ships
	all_ships = []
	for s in jo:
		tmp = ship()
		tmp.cond = s['api_cond']
		tmp.max_life = s['api_maxhp']
		tmp.life = s['api_nowhp']
		tmp.id = s['api_id']
		all_ships.append(tmp)

def parse_fleet(jo):
	global all_fleets
	global on_mission
	all_fleets = {}
	for i in range(4):
		li = [ele for ele in jo[i]['api_ship'] if ele is not -1]
		all_fleets[i+1] = li
		mis = jo[i]['api_mission']
		if mis[0]==0:
			on_mission[i+1] = -1
		else:
			on_mission[i+1] = long(mis[2])/1000

def parse_ndock(jo):
	global repair_dock
	for j in jo:
		repair_dock[j['api_id']] = j['api_ship_id']

############################
# layer2
############################

# def start_mission(deck_id,mission_id):
# 	api = '/kcsapi/api_req_mission/start'
# 	data = {'api_deck_id':deck_id,'api_mission_id':mission_id}
# 	jo = callAPI(api,data)
# 	try:
# 		backtime = long(jo['api_data']['api_complatetime'])/1000
# 		log('info','start_mission','fleet %d start mission %d'%(deck_id,mission_id))
# 		log('info','start_mission','and will return at %s'%(time.ctime(backtime)))
# 		return backtime
# 	except:
# 		log('debug','start_mission','backtime format convert failed')
# 		return None
# 	return None

# def fetch_fleet_ship_id(deck_ids):
# 	api = '/kcsapi/api_get_member/ship2'
# 	data = {'api_sort_order':2,'api_sort_key':1}
# 	jo = callAPI(api,data)
# 	try:
# 		for id in deck_ids:
# 			tmp = sorted(jo['api_data_deck'][id-1]['api_ship'])
# 			ship_id[id] = [ele for ele in tmp if not (ele==-1)]
# 			if jo['api_data_deck'][id-1]['api_mission'][0]==0:
# 				charge_fleet(id)
# 				time.sleep(3)
# 			else:
# 				tasks.append([id,jo['api_data_deck'][id-1]['api_mission'][2]/1000,0])
# 		log('info','fetch_fleet_ship_id','ship_id fetch succeed')
# 		log_to_file('info','fetch_fleet_ship_id',str(ship_id))
# 		return True
# 	except:
# 		log('debug','fetch_fleet_ship_id','json expected object missing')
# 		log_to_file('debug','fetch_fleet_ship_id',str(jo))
# 		return False
# 	return False

#############################
# kcs apis
#############################

def login_check():
	api = '/kcsapi/api_auth_member/logincheck'
	data = {}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','login_check','ok')
		return True
	return False

def material():
	api = '/kcsapi/api_get_member/material'
	data = {}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','material','ok')
		return True
	return False

def deck_port():
	api = '/kcsapi/api_get_member/deck_port'
	data = {}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','deck_port','ok')
		return True
	return False

def ndock():
	api = '/kcsapi/api_get_member/ndock'
	data = {}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','ndock','ok')
		parse_ndock(jo['api_data'])
		return True
	return False

def ship2():
	api = '/kcsapi/api_get_member/ship2'
	data = {'api_sort_order':2,'api_sort_key':1}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','ship2','ok')
		parse_ship(jo['api_data'])
		parse_fleet(jo['api_data_deck'])
		return True
	return False

def ship3():
	api = '/kcsapi/api_get_member/ship3'
	data = {'api_sort_order':2,'api_sort_key':1}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','ship3','ok')
		parse_ship(jo['api_data']['api_ship_data'])
		parse_fleet(jo['api_data']['api_deck_data'])
		return True
	return False

def basic():
	api = '/kcsapi/api_get_member/basic'
	data = {}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','basic','ok')
		return True
	return False

def result(deck_id):
	api = '/kcsapi/api_req_mission/result'
	data = {'api_deck_id':deck_id}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','fetch_mission_result','mission %s by fleet %d %s'%(jo['api_data']['api_quest_name'],deck_id,jo['api_result_msg']))
		return True
	else:
		log('debug','fetch_mission_result','fetch failed')
		return False

def useitem():
	api = '/kcsapi/api_get_member/useitem'
	data = {}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','useitem','ok')
		return True
	return False

def change(ship_id,ship_idx):
	api = '/kcsapi/api_req_hensei/change'
	data = {'api_ship_id':ship_id,'api_ship_idx':ship_idx,'api_id':1}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','change','ok')
		log('info','change','ship %d changed to %d'%(ship_id,ship_idx))
		return True
	return False

def deck():
	api = '/kcsapi/api_get_member/deck'
	data = {}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','deck','ok')
		parse_fleet(jo['api_data'])
		return True
	return False

def charge(deck_id):
	api = '/kcsapi/api_req_hokyu/charge'
	api_id_items = ','.join([str(ele) for ele in all_fleets[deck_id]])
	data = {'api_kind':3,'api_id_items':api_id_items}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','charge_fleet','charge fleet %d ok'%(deck_id))
		return True
	else:
		log('debug','charge_fleet','charge fleet %d failed'%(deck_id))
		return False

def nyukyo(ship_id,ndock_id,highspeed):
	api = '/kcsapi/api_req_nyukyo/start'
	data = {'api_ship_id':ship_id,'api_ndock_id':ndock_id,'api_highspeed':highspeed}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','nyukyo','ok')
		log('info','nyukyo','ship %d repairing at ndock %d'%(ship_id,ndock_id))
		return True
	return False

def mission_page(maparea):
	api = '/kcsapi/api_get_master/mission'
	data = {'api_maparea_id':maparea}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','mission_page','ok')
		return True
	return False

def api_start_mission(deck_id,mission_id):
	api = '/kcsapi/api_req_mission/start'
	data = {'api_deck_id':deck_id,'api_mission_id':mission_id}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','start_mission','ok')
		backtime = long(jo['api_data']['api_complatetime'])/1000
		log('info','start_mission','fleet %d start mission %d'%(deck_id,mission_id))
		log('info','start_mission','and will return at %s'%(time.ctime(backtime)))
		return True
	return False

def record():
	api = '/kcsapi/api_get_member/record'
	data = {}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','record','ok')
		return True
	return False

def mapinfo():
	api = '/kcsapi/api_get_master/mapinfo'
	data = {}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','mapinfo','ok')
		return True
	return False

def mapcell(mapinfo_no=2,maparea_id=3):
	api = '/kcsapi/api_get_master/mapcell'
	data = {'api_mapinfo_no':mapinfo_no,'api_maparea_id':maparea_id}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','mapcell','ok')
		return True
	return False

def map_start(mapinfo_no=2,maparea_id=3,deck_id=1,formation_id=1):
	api = '/kcsapi/api_req_map/start'
	data = {'api_formation_id':formation_id,'api_deck_id':deck_id,'api_mapinfo_no':mapinfo_no,'api_maparea_id':maparea_id}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','map_start','ok')
		return True
	return False

def battle(formation=1):
	api = '/kcsapi/api_req_sortie/battle'
	data = {'api_formation':formation}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','battle','ok')
		global midnight_flag
		midnight_flag = jo['api_data']['api_midnight_flag']
		log('info','battle','yasen? %d'%(midnight_flag))
		return True
	return False

def battle_result():
	api = '/kcsapi/api_req_sortie/battleresult'
	data = {}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','battle_result','ok')
		return True
	return False

def slotitem():
	api = '/kcsapi/api_get_member/slotitem'
	data = {}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','slotitem','ok')
		return True
	return False

def yasen():
	api = '/kcsapi/api_req_battle_midnight/battle'
	data = {}
	jo = callAPI(api,data)
	if jo is not None:
		log('info','yasen','ok')
		return True
	return False

#############################
# user actions
#############################

def go_to_home() :
	login_check()
	material()
	deck_port()
	ndock()
	ship3()
	basic()

def fetch_mission_result(deck_id):
	result(deck_id)
	deck_port()
	basic()
	ship2()
	material()
	useitem()

def go_to_repair():
	ndock()
	ship2()
	useitem()

# highspeed: 0 for no, 1 for yes
def repair(ship_id,ndock_id,highspeed):
	nyukyo(ship_id,ndock_id,highspeed)
	ship2()
	material()
	ndock()

def go_to_change():
	pass
	# nothing needed

def change_ship(ship_id,ship_idx):
	change(ship_id,ship_idx)
	deck()

def go_to_charge():
	pass
	# nothing needed

def charge_fleet(deck_id):
	charge(deck_id)
	ship2()

def go_to_mission_page(mission):
	mission_page(int(mission/8+1))

def start_mission(deck_id,mission_id):
	api_start_mission(deck_id,mission_id)
	deck()

def write_battle_cnt():
	global battle_cnt
	if battle_cnt==0:
		return
	else:
		f = open(counter_file,'r')
		last = ''
		while True:
			line = f.readline()
			if not len(line)==0:
				last = line
			else:
				break;
		f.close()

		f = open(counter_file,'a')
		if len(last)==0:
			s = '%d %d\n'%(time.localtime().tm_mday,battle_cnt)
			f.write(s)
		else:
			last = last[:-1]
			day = int(last.split(' ')[0])
			old_cnt = int(last.split(' ')[1])
			if day==time.localtime().tm_mday:
				battle_cnt = old_cnt+battle_cnt
			s = '%d %d\n'%(time.localtime().tm_mday,battle_cnt)
			f.write(s)
		f.close()

def check_battle_condition():
	cond_wait = 1200
	# check ship cond
	main_fleet = [ele for ele in all_fleets[1] if ele not in all_ss]
	min_cond = 100
	for s in all_ships:
		if s.id in main_fleet:
			min_cond = min(min_cond,s.cond)	
	if min_cond<30:
		cond_wait = (33-min_cond)*60
	else:
		cond_wait = 0
	for s in all_ships:
		if s.id in main_fleet and s.id in repair_dock.values():
			cond_wait = 600 

	ss_wait = 600
	# check ss state
	ss = [ele for ele in all_fleets[1] if ele in all_ss][0]
	ss_ship = [ele for ele in all_ships if ele.id in all_ss]
	for s in ss_ship:
		if ss==s.id:
			ss = s
			break
	if ss.id not in repair_dock.values() and ss.life*2>=ss.max_life and ss.cond>=30:
		ss_wait = 0
	else:
		ok_flag = False
		for s in ss_ship:
			if s.id not in repair_dock.values() and (s.life*2<s.max_life or s.cond<30):
				if s.life<s.max_life:
					# repair s
					for i in range(4):
						if not repair_dock.__contains__(i+1) or repair_dock[i+1]==0:
							go_to_repair()
							repair(s.id,i+1,0)
							break
			elif s.id not in repair_dock.values() and not ok_flag: # s is available
				change_ship(s.id,ss_loc)
				ss_wait = 0
				ok_flag = True
	wait_time = max(ss_wait,cond_wait)
	if wait_time is 0:
		return True
	else:
		global sleep_time
		sleep_time = min(sleep_time,wait_time)
		return False

def go_to_battle():
	# charge fleet 1
	go_to_charge()
	charge_fleet(1)
	# start battle
	record()
	mapinfo()
	mapcell()
	map_start()
	battle()
	if midnight_flag==1:
		yasen()
	# battle step
	battle_result()
	ship2()
	slotitem()
	deck()
	# battle end
	go_to_home()

#############################
# control logic
#############################

def auto_mission():
	global sleep_time
	# get mission result
	for fleet_id in mission.keys():
		if on_mission[fleet_id] is not -1:
			if time.time() > on_mission[fleet_id]+5:
				fetch_mission_result(fleet_id)
	# go_to_home()
	# charge fleets
	for fleet_id in mission.keys():
		if on_mission[fleet_id]==-1:
			charge_fleet(fleet_id)
	# set out for mission
	for mis in mission.items():
		if on_mission[mis[0]]==-1:
			go_to_mission_page(mis[1])
			start_mission(mis[0],mis[1])
	go_to_home()
	for fleet_id in mission.keys():
		if on_mission[fleet_id] is not -1:
			sleep_time = min(sleep_time,on_mission[fleet_id]+5-time.time())

def auto_battle():
	while check_battle_condition():
		go_to_battle()
		global battle_cnt
		battle_cnt += 1

def auto_repair():
	repair_list = [ele for ele in all_ships if ele.life<ele.max_life and ele.id not in repair_dock.values()]
	repair_list.sort(key=lambda x:float(x.life)/x.max_life,reverse=True)
	for s in repair_list:
		# find an empty dock
		for i in range(4):
			if repair_dock[i+1]==0:
				go_to_repair()
				if s.id in all_fleets[1] and s.id not in all_ss:
					repair(s.id,i+1,1)
				else:
					repair(s.id,i+1,0)
				break
	return True

def main():
	go_to_home()
	if enable_auto_mission:
		auto_mission()
	if enable_auto_battle:
		auto_battle()
	if enable_auto_repair:
		auto_repair()
	global sleep_time
	if sleep_time<0:
		log('info','main','error with sleep time')
		sleep_time = 60
	write_battle_cnt()
	write_sleep_time()

if __name__ == '__main__':
	main()
	# pass