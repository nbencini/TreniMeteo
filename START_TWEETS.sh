#!/bin/bash
pid_file='/mnt/volume_fra1_01/logs/00_stream_tweets.pid'
if [ ! -s "$pid_file" ] || ! kill -0 $(cat $pid_file) > /dev/null 2>&1; then
  echo $$ > "$pid_file"
  exec nohup python3 /root/viaggiatreno/00_stream_tweets.py >> /mnt/volume_fra1_01/logs/00_stream_tweets.log 2>&1 & echo $! > /mnt/volume_fra1_01/logs/00_stream_tweets.pid
fi
