#!/bin/bash

session=$1

tmux new-session -d -s "avmpi_${session}"
# window 0 runs the code
tmux rename-window -t "avmpi_${session}" "run"
tmux send-keys -t "run" "cd .." C-m
tmux send-keys -t "run" "source venv/bin/activate" C-m
tmux send-keys -t "run" "cd avmpi_scripts" C-m
# window 1 is git
tmux new-window -t "avmpi_${session}":1 -n "git"
tmux send-keys -t "git" "cd .." C-m
tmux send-keys -t "git" "source venv/bin/activate" C-m
tmux send-keys -t "git" "git fetch" C-m
tmux send-keys -t "git" "git status" C-m
if [ $session == "dev" ]
then
    # window 2 is script
    tmux new-window -t "avmpi_${session}":2 -n "script"
elif [ $session == "tests" ]
then
    # window 2 is script
    tmux new-window -t "avmpi_${session}":2 -n "script"
    tmux send-keys -t "script" "cd .." C-m
    tmux send-keys -t "script" "source venv/bin/activate" C-m
    tmux send-keys -t "script" "cd avmpi_scripts" C-m
    # window 3 is the tests we're writing
    tmux new-window -t "avmpi_${session}":3 -n "tests"
    tmux send-keys -t "tests" "cd .." C-m
    tmux send-keys -t "tests" "source venv/bin/activate" C-m
    tmux send-keys -t "tests" "cd tests" C-m
fi

tmux attach-session -t "avmpi_${session}":1
