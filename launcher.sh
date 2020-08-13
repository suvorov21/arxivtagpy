#!/usr/bin/env bash

cd arXivTag
mkdir -p ../log
python3 server.py > ../log/log.log 2>&1 &
PID=$!
echo "Running a flask server with PID $PID"
echo "To stop server use 'kill -9 $PID'"
sensible-browser http://127.0.0.1:8880/ &
cd ../
