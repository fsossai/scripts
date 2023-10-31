#!/bin/bash

color='\033[0;35m'
reset='\033[0m'

if [[ $# < 2 ]]; then
  echo "Usage: $0 FILE COMMAND"
  exit 1
fi

input=$1
cmd=$2
interval=0.2

clear

echo -e "${color}$(date)${reset}"
eval "$cmd"

pre=0
post=`md5sum $input`

while true; do
  mod=false
  while [[ ! "$mod" == "1" ]]; do
    pre=$post
    post=`md5sum $input`
    [[ "$pre" == "$post" ]]
    mod="$?"
    sleep $interval
  done
echo "Modified"
clear
echo -e "${color}$(date)${reset}"
eval "$cmd"
sleep $interval
done
