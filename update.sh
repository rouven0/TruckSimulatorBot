git pull
kill -1 $(ps aux | grep uu | cut -d " " -f7 | head -1)
