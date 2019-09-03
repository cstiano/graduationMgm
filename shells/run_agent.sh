#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
graduationmgm/lib/HFO_mgm/bin/HFO --fullstate --no-logging --headless --defense-agents=3 --offense-npcs=3 --defense-npcs=1 --offense-team=helios --trials $1 &
sleep 10
# Sleep is needed to make sure doesn't get connected too soon, as unum 1 (goalie)
python ./agents/agent.py &
sleep 5
python ./agents/agent.py &
sleep 5
python ./agents/agent.py &
sleep 5

# The magic line
#   $$ holds the PID for this script
#   Negation means kill by process group id instead of PID
trap "kill -TERM -$$" SIGINT
wait