git pull
kill -1 $(ps aux | grep TruckSimulatorBot | head -1 | perl -n -e'/\w* *(\d*)/ && print $1'
