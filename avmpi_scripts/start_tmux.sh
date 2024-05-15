#!/bin/bash

session=$1

if [ $session == "dev" ]
then
    tmux new-session -d -s $session
    #window 0 runs the code
    tmux rename-window -t $session "run"
    tmux send-keys -t "run" "cd .." C-m
fi

tmux attach-session -t $session:0
