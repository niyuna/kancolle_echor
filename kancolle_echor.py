import time
import requests as req
import json
import sys
from threading import Timer as Timer
from random import random
import math


########################
# user define config
mission = {2:2, 3:5, 4:37} # {2:6, 3:5, 4:38}
api_token = '49eedb78a2ec7df25921ec67fc9beb31b12c09a9'
api_verno = 1
host = '125.6.189.135'
member_id = '13063716'
log_file = r'log'
api_token_file = r'api_token'
sleep_time_file = r'sleep_time'
counter_file = r'counter'
connection_retry_time = 5
enable_auto_mission = True
enable_auto_battle = False
enable_auto_repair = True
go_to_tokyo = False
enable_proxy = False # when network sucks, use a local proxy to avoid catgod
ss_id = [695, 93, 365, 704, 385, 1917]
ss_loc = 1 # 0~5
# these ships will be repaired when they are less than 50% max HP
protection_id = [744, 31, 118, 648, 913]
########################

########################
# config
baseurl = 'http://' + host
headers = {
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,ja;q=0.2,zh-TW;q=0.2',
    'Referer': baseurl+'/kcs/Core.swf?version=2.0.9', # WARNING!!! version is fixed
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; WOW64; Trident/6.0),',
    'Host': host,
    'Origin': baseurl,
    'Connection': 'Keep-Alive'
}

# local proxy setting
proxy_dict = {
    'http': 'http://127.0.0.1:8087',
    'https': '127.0.0.1:8087',
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
midnight_flag = 0 # midnight flag for every battle
battle_cnt = 0 # record the default battle count into count file 
sleep_time = 1800
ship_cnt = 0

res = [0, 0, 0, 0]
construct_util = 0
repair_util = 0


def log(tag,role,message):
    print '%s # %s # %s # %s'%(time.ctime(),tag.upper(),role.upper(),message)


def log_to_file(tag,role,message):
    f = open(log_file,'a')
    output = '%s # %s # %s # %s'%(time.ctime(),tag.upper(),role.upper(),message)
    f.write(output+'\n')
    f.close()


def write_sleep_time():
    f = open(sleep_time_file,'w')

    from random import choice
    global sleep_time
    sleep_time += choice(range(15,30))

    f.write(str(int(sleep_time)))
    f.close()


def print_resource():
    print 'resource now:'
    print str(res[0]).rjust(6),str(res[2]).rjust(6)
    print str(res[1]).rjust(6),str(res[3]).rjust(6)
    print 'repair util now:'
    print repair_util

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
    payload = {'api_token':api_token,'api_verno':api_verno}
    payload.update(data)
    url = baseurl+api
    try:
        if enable_proxy:
            r = req.post(url,data=payload,headers=headers,timeout=15,proxies=proxy_dict)
        else:
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
            time.sleep(5)
    log('info','callAPI','reach max limit, restart system in 60s')
    global sleep_time
    sleep_time = 3600
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
    global ship_cnt
    ship_cnt = len(all_ships)


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


def parse_material(jo):
    global resource
    global repair_util
    res[0] = jo[0]['api_value']
    res[1] = jo[1]['api_value']
    res[2] = jo[2]['api_value']
    res[3] = jo[3]['api_value']
    repair_util = jo[5]['api_value']


# parse `port` api call
def parse_port(jo):
    parse_ship(jo['api_ship'])
    parse_ndock(jo['api_ndock'])
    parse_fleet(jo['api_deck_port'])
    parse_material(jo['api_material'])

#############################
# kcs apis
#############################

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
    data = {'spi_sort_order':2, 'api_sort_key':5}
    jo = callAPI(api,data)
    if jo is not None:
        log('info','ship2','ok')
        parse_ship(jo['api_data'])
        parse_fleet(jo['api_data_deck'])
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


# api_port_helper
def gI(s):
    return int(s, 31)


# api_port_helper
def cN():
    return str(int(math.floor(random() * 10)))


def tI():
    return int(time.time() * 1000)


def cR():
    return 1 + int(math.floor(random() * 9))


def cM(n):
    return str(n)


def cG(o):
    return int(o)


def cS():
    return 1000 + int(math.floor(random() * 8999));


# get api_port using a so-called `_$` method in core_ldtixityfwi
def generate_api_port_dollar():
    SF = [1802, 9814, 5616, 4168, 7492, 5188, 2765, 8118, 6381, 7636]
    u = int(member_id)
    ret = cM((cR() * 1000) + (u % 1000))
    ret += cM((9999999999 - int(math.floor(tI() / 1000)) - u) * cG(SF[u%10]))
    ret += cM(cS())
    log('info', 'port', ret)
    return ret


# the old method to get api_port, `_`
def generate_api_port():
    # _local3 = ["16o", "1sc", "2j6", "371", "50e", "5dp", "6hi", "89a", "8dc", "9nf", "118"] # core_2_0_1
    _local3 = ["315", "50e", "7ig", "209", "63e", "9c6", "6cj", "3ge", "928", "1h9", "118"]; # core_2_0_9
    u = int(member_id)
    ret = ''
    ret += str(gI(_local3[10]) + (u % gI(_local3[10])))
    ret += str((9999999999 - int(math.floor(tI() / gI(_local3[10]))) - u) * gI(_local3[(u % 10)]))
    ret += cN() * 4
    log('info', 'port', ret)
    return ret


# new method for api_port
def port():
    api = '/kcsapi/api_port/port'
    data = {'spi_sort_order':2, 'api_sort_key':5, 'api_port':generate_api_port_dollar()}
    jo = callAPI(api, data)
    if jo is not None:
        log('info', 'port', 'parsing data')
        parse_port(jo['api_data'])
        log('info', 'port', 'ok')
        return True
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
    data = {'api_kind':3, 'api_id_items':api_id_items, 'api_onslot':1}
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
        log('info','nyukyo','ship %d repairing at ndock %d with %d highspeed'%(ship_id,ndock_id,highspeed))
        return True
    return False


def mission_page():
    api = '/kcsapi/api_get_member/mission'
    data = {}
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


def mapinfo():
    api = '/kcsapi/api_get_member/mapinfo'
    data = {}
    jo = callAPI(api,data)
    if jo is not None:
        log('info','mapinfo','ok')
        return True
    return False


def mapcell(mapinfo_no=3,maparea_id=3):
    api = '/kcsapi/api_get_member/mapcell'
    data = {'api_mapinfo_no':mapinfo_no,'api_maparea_id':maparea_id}
    jo = callAPI(api,data)
    if jo is not None:
        log('info','mapcell','ok')
        return True
    return False


def sortie_conditions():
    api = '/kcsapi/api_get_member/sortie_conditions'
    data = {}
    jo = callAPI(api, data)
    if jo is not None:
        log('info', 'sortie_conditions', 'ok')
        return True
    return False


def map_start(mapinfo_no=3,maparea_id=3,deck_id=1,formation_id=1):
    api = '/kcsapi/api_req_map/start'
    data = {'api_formation_id':formation_id,'api_deck_id':deck_id,'api_mapinfo_no':mapinfo_no,'api_maparea_id':maparea_id}
    jo = callAPI(api,data)
    if jo is not None:
        log('info','map_start','ok')
        return jo['api_data']['api_no']
    return False


def map_next():
    api = '/kcsapi/api_req_map/next'
    data = {'api_recovery_type':0}
    jo = callAPI(api,data)
    if jo is not None:
        log('info','map_next','ok')
        log('info','map_next','next is %s %s'%(jo['api_data']['api_next'],jo['api_data']['api_no']))
        # usually 1 4
        return jo['api_data']['api_no']
    return False


def battle(formation=1):
    api = '/kcsapi/api_req_sortie/battle'
    data = {'api_formation':formation, 'api_recovery_type':0}
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
        log('info','battle_result','enemy %s rank %s'%(jo['api_data']['api_enemy_info']['api_deck_name'],jo['api_data']['api_win_rank']))
        if 'api_get_ship' in jo['api_data']:
            log('info', 'battle_result', 'get ship %s'%jo['api_data']['api_get_ship']['api_ship_name'])
        return True
    return False


def slotitem():
    api = '/kcsapi/api_get_member/slot_item'
    data = {}
    jo = callAPI(api,data)
    if jo is not None:
        log('info','slotitem','ok')
        return True
    return False


def unsetslot():
    api = '/kcsapi/api_get_member/unsetslot'
    data = {}
    jo = callAPI(api,data)
    if jo is not None:
        log('info','unsetslot','ok')
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
 
def print_fleet_state(deck_id):
    flag = True
    for s in all_ships:
        if s.id in all_fleets[deck_id]:
            print s.id,'%d/%d/%d'%(s.life,s.max_life,s.cond),s.id in repair_dock.values()
            if s.life*3<s.max_life or s.cond<30 or s.id in repair_dock.values():
                flag = False
    return flag


def go_to_home() :
    port()


def battle_home():
    slotitem()
    unsetslot()
    useitem()
    port()


def fetch_mission_result(deck_id):
    result(deck_id)
    port()
    useitem()


# checked: useless, change to dummy
def go_to_repair():
    ndock()
    

# highspeed: 0 for no, 1 for yes
def repair(ship_id,ndock_id,highspeed):
    nyukyo(ship_id,ndock_id,highspeed)
    
def go_to_change():
    pass


def change_ship(ship_id,ship_idx):
    change(ship_id,ship_idx)
    deck()


def go_to_charge():
    pass


def charge_fleet(deck_id):
    charge(deck_id)


def go_to_mission_page(mission):
    mission_page()


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

def check_tokyo_condition():
    # check life condition
    life_wait = 0
    for s in all_ships:
        if s.id in all_fleets[1]:
            if s.life*3<s.max_life:
                life_wait = 180
                break

    # check cond
    cond_wait = 0
    for s in all_ships:
        if s.id in all_fleets[1]:
            if s.cond<30:
                cond_wait = max(cond_wait,(33-s.cond)*60)

    wait = max(life_wait,cond_wait)
    log('info','check_t_cond','wait time is %d'%(wait))
    global sleep_time
    sleep_time = min(sleep_time,wait)
    return wait<=0
    
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
                            go_to_home()
                            break
            elif s.id not in repair_dock.values() and not ok_flag: # s is available
                change_ship(s.id,ss_loc)
                ss_wait = 0
                ok_flag = True
    wait_time = max(ss_wait,cond_wait)
    for s in all_ships:
        if s.life*2<s.max_life and s.id in all_fleets[1] and s.id not in all_ss:
            wait_time = 60
    if wait_time is 0:
        return True
    else:
        global sleep_time
        sleep_time = min(sleep_time,wait_time)
        log("info",'check_b_cond','wait_time is %d'%(wait_time))
        return False


def go_to_battle_23():
    battle_point = [1,3,5,9,10,11]
    end_point = [8,9,10,11]
    point_now = 0

    go_to_charge()
    charge_fleet(1)
    time.sleep(5)
    go_to_home()
    mapinfo()
    time.sleep(3)
    mapcell(3,2)
    point_now = map_start(3,2)

    while True:
        if point_now in battle_point:
            battle()
            time.sleep(15)
            if point_now in [3,9,10,11] and midnight_flag==1:
                yasen()
                time.sleep(10)
            battle_result()
            time.sleep(10)
            ship2()
            if not print_fleet_state(1):
                break
        if point_now in end_point:
            break
        else:
            time.sleep(3)
            point_now = map_next()
        time.sleep(3)

    time.sleep(3)
    battle_home()

def plan_23():
    # point 6 <=> point 12
    go_to_home()
    time.sleep(5)
    while not print_fleet_state(1):
        print 'restore cond for 360s'
        time.sleep(360)
        go_to_home()
    while True:
        go_to_battle_23()
        print 'trying to repair'
        auto_repair_23()
        time.sleep(3)
        go_to_home()    
        auto_mission()
        go_to_home()
        print_resource()
        while not print_fleet_state(1):
            print 'restore cond for 360s'
            time.sleep(360)
            go_to_home()
        print 'sleeping for 15s'
        time.sleep(15)


def go_to_battle_11():
    go_to_charge()
    charge_fleet(1)
    time.sleep(5)
    go_to_home()
    mapinfo()
    time.sleep(3)
    mapcell(1,1)
    map_start(1,1)
    battle()
    time.sleep(10)
    if midnight_flag==1:
        yasen()
        time.sleep(10)
    battle_result()
    time.sleep(10)
    
    # choose to fight another battle
    ship2()
    map_next()
    time.sleep(10)
    battle()
    time.sleep(10)
    if midnight_flag==1:
        yasen()
        time.sleep(10)
    battle_result()
    time.sleep(10)
    battle_home()


# map_next print '0 2' means not boss ponit
def plan_a():
    go_to_home()
    print_fleet_state(1)
    time.sleep(5)
    while True:
        go_to_battle_11()
        print 'trying to repair'
        auto_repair_23()
        go_to_home()
        auto_mission()
        while not print_fleet_state(1):
            print 'restore cond for 300s'
            time.sleep(300)
            go_to_home()
        print("sleeping 15s")
        time.sleep(15)


def go_to_battle_e1():
    go_to_charge()
    charge_fleet(1)

    mapinfo()
    sortie_conditions()
    mapcell(mapinfo_no=1, maparea_id=26)
    map_start(mapinfo_no=1, maparea_id=26)
    
    # point A
    battle()
    time.sleep(15)
    # no yasen
    battle_result()
    time.sleep(5)
    ship2() # may be dangerouse!
    # check state
    if not print_fleet_state(1):
        battle_home()
        time.sleep(5)
        return

    map_next()
    print 'assert api_next:1 api_no:2'
    time.sleep(3)
    # point B
    battle()
    time.sleep(15)
    # no yasen
    battle_result()
    time.sleep(5)
    ship2() # may be dangerouse!
    # check state
    if not print_fleet_state(1):
        battle_home()
        time.sleep(5)
        return

    map_next()
    print 'assert api_next:2 api_no:3'
    time.sleep(3)
    # point D
    battle()
    time.sleep(15)
    if midnight_flag==1:
        yasen()
        time.sleep(10)
    battle_result()
    time.sleep(5)
    ship2() # may be dangerouse!
    # check state
    if not print_fleet_state(1):
        battle_home()
        time.sleep(5)
        return

    map_next() 
    print 'assert api_next:0 api_no:10'
    time.sleep(3)
    # point H
    battle()
    time.sleep(15)
    if midnight_flag==1:
        yasen()
        time.sleep(10)
    battle_result()
    time.sleep(5)

    battle_home()


def plan_hatsukaze():
    global ship_cnt
    go_to_home()
    while not print_fleet_state(1):
        print 'restore cond for 360s'
        time.sleep(360)
        go_to_home()
    time.sleep(5)
    while True:
        log('info','main','ship cnt %d'%(ship_cnt))
        if ship_cnt > 94:
            return
        go_to_battle_e1()
        time.sleep(5)
        print 'trying to repair'
        auto_repair_23()
        go_to_home()
        auto_mission()
        while not print_fleet_state(1):
            print 'restore cond for 360s'
            time.sleep(360)
            go_to_home()
        print('sleeping 15s')
        time.sleep(15)


def plan_tokyo():
    go_to_charge()
    charge_fleet(1)

    mapinfo()
    mapcell(4,5)
    map_start(4,5)
    
    # point A
    battle()
    time.sleep(15)
    # no yasen
    battle_result()
    ship2()
    
    # check state
    if not print_fleet_state(1):
        battle_home()
        time.sleep(5)
        return

    # point E
    map_next()
    time.sleep(3)

    # point H
    map_next()
    time.sleep(3)
    battle()
    time.sleep(15)
    # no yasen
    battle_result()
    ship2()
    # check state
    if not print_fleet_state(1):
        battle_home()
        time.sleep(5)
        return

    # point M
    map_next()
    time.sleep(3)

    # point O
    map_next()
    time.sleep(3)
    battle()
    time.sleep(15)
    if midnight_flag==1:
        yasen()
        time.sleep(10)
    battle_result()
    ship2()
    
    battle_home()
    time.sleep(1)

def go_to_battle():
    # charge fleet 1
    go_to_charge()
    charge_fleet(1)
    # start battle
    mapinfo()
    sortie_conditions()
    mapcell()
    map_start()
    # map_next()
    battle()
    time.sleep(15)
    if midnight_flag==1:
        yasen()
        time.sleep(10)
    # battle step
    battle_result()
    # battle end
    battle_home()

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
                time.sleep(3)
    # charge fleets
    for fleet_id in mission.keys():
        if on_mission[fleet_id]==-1:
            charge_fleet(fleet_id)
            time.sleep(3)
    # set out for mission
    for mis in mission.items():
        if on_mission[mis[0]]==-1:
            go_to_mission_page(mis[1])
            start_mission(mis[0],mis[1])
            time.sleep(3)
    go_to_home()
    for fleet_id in mission.keys():
        if on_mission[fleet_id] is not -1:
            sleep_time = min(sleep_time,on_mission[fleet_id]+5-time.time())


def auto_battle():
    while check_battle_condition():
        go_to_battle()
        time.sleep(3)
        global battle_cnt
        battle_cnt += 1


def r_helper(x):
    if x in all_fleets[1]:
        return 1
    else:
        return float(x.life)/x.max_life


def auto_repair_23():
    repair_list = [ele for ele in all_ships if ele.id in all_fleets[1]  and ele.life*2<ele.max_life and ele.id not in repair_dock.values()]
    for s in repair_list:
        # find an empty dock
        for i in range(4):
            if repair_dock[i+1]==0:
                go_to_repair()              
                repair(s.id,i+1,1)
                go_to_home()
                break
        time.sleep(3)
    return True


def auto_repair():
    repair_list = [ele for ele in all_ships if ele.life<ele.max_life and ele.id not in repair_dock.values()]
    repair_list = [ele for ele in repair_list if (ele.id in all_fleets[1] and (ele.life*2<=ele.max_life or ele.id in all_ss or (ele.life*2<ele.max_life and ele.id in protection_id))) or ele.id not in all_fleets[1]]
    repair_list.sort(key=lambda x:r_helper(x),reverse=True) # ships in fleet 1 has greater priority
    for s in repair_list:
        # find an empty dock
        for i in range(4):
            if repair_dock[i+1]==0:
                go_to_repair()
                if s.id in all_fleets[1] and s.id not in all_ss:
                    repair(s.id,i+1,1)
                else:
                    repair(s.id,i+1,0)
                go_to_home()
                break
        time.sleep(3)
    return True


def main():
    go_to_home()
    if enable_auto_mission:
        auto_mission()
    time.sleep(3)
    if go_to_tokyo:
        while check_tokyo_condition():
            log('info','main','all ship cnt %d'%(ship_cnt))
            if ship_cnt>97:
                break
            print_fleet_state(1)
            plan_tokyo()
            global battle_cnt
            battle_cnt += 1
            time.sleep(5)
    if enable_auto_battle:
        auto_battle()
    time.sleep(3)
    if enable_auto_repair:
        auto_repair()
    global sleep_time
    if sleep_time<0:
        log('info','main','error with sleep time %d'%(sleep_time))
        sleep_time = 60
    write_battle_cnt()
    write_sleep_time()
    print_fleet_state(1)
    print_resource()

if __name__ == '__main__':
    main()
    # pass