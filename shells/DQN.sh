#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
poetry run graduationmgm/lib/HFO_mgm/bin/HFO --fullstate --no-logging --headless --defense-agents=1 --offense-npcs=1 --defense-npcs=1 --trials $1 &
sleep 10
# Sleep is needed to make sure doesn't get connected too soon, as unum 1 (goalie)
poetry run python ./agents/agent_1.py &
sleep 5

# The magic line
#   $$ holds the PID for this script
#   Negation means kill by process group id instead of PID
trap "kill -TERM -$$" SIGINT
wait