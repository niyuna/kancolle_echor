kancolle_echor
=========================

Simple and handy script that automates kancolle.
### 6.6 update
new `api_port` generation method updated.

### Features in ver. Amatsukaze
1. Expedition.

	The most basic feature. Set the correct ships for your expeditions, and the script will set out your fleets,
	get them back and charge them.

2. Auto repair. Repair your ship in the reversed order of time to use, additionally, ships in fleet 1 will have higher priority.
And if your ship in fleet one is below 50% max HP, a repair utility will be used to repair it.

3. Auto battle in 1-1/3-3a/3-2a/5-4f.

	For 3-2a/3-3a(default), use default scheduler mode to run. And to use this, you have to supply some configs. 

		* ss_id: the ship ids of your submarine
		* ss_loc: the place to hold your submarine

	Submarines are used as tanks to absorb damage in battle, or it's not efficient enough to repeat this.
	Create a file named counter to store 3-3-a battle count. Place your submarine at ss_loc
	and the script will change ships if the ship has too low life or in bad condition. Only when all of your
	ships in fleet 1 are in good condition will the script go to battle.

	For other maps, run plan_a/plan_23/plan_tokyo/plan_hatsukaze methods independently, not from scheduler. I recommend the following way. Replace the last line of the script with `pass` and run 
	
	```
	python -i kancolle_echor.py
	``` 
	
	This will make you enter the interactive mode of python runtime, and you can easily run single method or debug the script. If you know some python, you can easily write a method to auto battle from these examples.


### Requirements
The python script need python 2.7 and python `requests` lib, you can simply install it using:

```
>>> pip install requests
```

And use scheduler.bat under windows, scheduler.sh under linux. 

### How to use
1. First time config your host due to your server in kancolle_echor.py. Change value of **host** to your server ip address. This address won't change.

	Now due to the game's upgrade you have to supply another argument, your **member_id**. Get this using a web debugger, this string can be found in the response of `port` HTTP request.

2. Every time before you use this script:

	1. Config your mission plan in kancolle_echor.py. Change value of **mission**. For example, 2:17, 3:3, 4:5 means fleet 2 set for mission 17, fleet 3 set for mission 3 and fleet 4 set for mission 5.

	2. Ensure your **api_token** is the latest, this means you didn't open the game page another time after you fetch this from the game page. Note that this token usually expire in 24h, but may lasts longer if you are using a Japanenes ip address.
	If not, open the game page using a browser, place the api_token into the **api_token** file. Then don't kill the game page, just leave it there.

3. Run scheduler.bat/sh to start the script.


### How to get the host address and api_token?
Before you run this script, you should open the game page using a browser. If you are using chrome or ie, press F12 at the game loading page and search for **api_token** in the source code part. You should see a url like:
```
http://your_host_ip_address/MainD2.swf?api_token=your_api_token&api_starttime=****
```

### Attention
1. When the script is running, DON'T PLAY GAME ON GAME PAGE. If you do so, the game page may tell you network error occured.
2. After exiting the game page, refresh the game page.(this will cause the old api_token expired, so you should fill the api_token every time you run this script)
3. If you are running on windows xp or something older, remember to change line 5 of scheduler.bat to 
```
ping -n %SLEEP_TIME% 127.0.0.1 > nul
```
4. This script is used at your own risk. Contact me if you have any suggestion about the script itself. 

5. The upgrade before spring event make a lot changes, I discuss some of these in [my blog][ref](in Chinese).

[ref]: http://www.yurapoi.com/?p=1173001