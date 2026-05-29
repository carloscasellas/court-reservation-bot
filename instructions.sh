source venv/bin/activate
truncate -s 0 log/instructions.log
timedatectl > log/instructions.log
rm -rf videos/*
python goldman-bot.py
python goldman-bot.py
aws s3 cp videos/ s3://goldman-bot-video-retrieval/ --recursive
deactivate
