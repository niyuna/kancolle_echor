n=1
while (( n <= 1000))
do
	python kancolle_echor.py
	n=$(( n+1 ))
	read st < sleep_time
	date
	echo "to sleep $st seconds"
	sleep $st
done
