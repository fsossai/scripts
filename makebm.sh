#!/bin/bash

# Parameters:
#
# cmd         e.g.: "/home/user/abc.out <<< /home/user/data.txt"
# runs        e.g.: 10
# maxt        e.g.: 56
# trange      e.g.: "1,2,4,8,16,24,28,32,40"
# prefix      e.g.: mymachine
# postfix     e.g.: abc
# realtime    y | n
# phase       e.g.: "Kernel"

timer_start=$(date +%s.%3N)
timestamp=$(date +%y%m%d-%H%M)

if [[ -z $cmd ]]; then
  echo "ERROR: no cmd provided"
  exit 1
fi

# setting default values
if [[ -z $runs ]]; then runs=3; fi
if [[ -z $realtime ]]; then realtime="n"; fi
if [[ -z $phase ]]; then phase="Kernel"; fi

if [[ -n $prefix$name$postfix ]]; then
  outfile="$prefix$name$postfix.csv"
else
  outfile="bm_${timestamp}.csv"
fi

if [[ -z $trange ]]; then
  space=$(seq 1 $maxt)
else
  space=$(sed "s/,/ /g" <<< $trange)
fi

# creating the thread space
space=()
if [[ -n $trange ]]; then
  for t in ${trange//,/ }; do
    if [[ -n $maxt ]]; then
      if (( $t <= $maxt )); then
        space+=($t)
      fi
    else
      space+=($t)
    fi
  done
else
  if [[ -n $maxt ]]; then
    space=( $(seq 1 $maxt) )
  else
    space=(1)
  fi
fi

if (( ${#space[@]} == 0 )); then
  echo "WARNING: empty intersection. Please review 'trange' and 'maxt'"
  space=(1)
fi

echo "name        = $name"
echo "cmd         = $cmd"
echo "runs        = $runs"
echo "maxt        = $maxt"
echo "trange      = $trange"
echo "realtime    = $realtime"
echo "phase       = $phase"
echo "outfile     = $outfile"
echo "threads     = { ${space[@]} }"
echo

echo "threads,time" > $outfile

for threads in ${space[@]}; do
  total_time=0
  E2=0
  mean2=0

  export OMP_NUM_THREADS=$threads

  echo "OMP_NUM_THREADS = $threads"
  echo "KMP_AFFINITY    = $KMP_AFFINITY"
  echo "OMP_PLACES      = $OMP_PLACES"

  for ((i=1; i<=runs; i++)); do
    printf "\tt=%s run %2i/%i : " $threads $i $runs

    if [[ $realtime == "y" ]]; then
      current_time=$({ time -p eval "$cmd" > /dev/null ; } 2>&1 | grep real | egrep -o "[0-9]*(\.[0-9]+)?")
      rc=$?
      current_time=$(echo "$current_time*1000" | bc)
    else
      cmd_out=$(eval "$cmd")
      rc=$?
      current_time=$(echo "$cmd_out" | grep -i $phase | egrep -o "[0-9]*(\.[0-9]+)?")
    fi

    echo "$threads,$current_time" >> $outfile
    printf "%.3f ms (rc=%i)\n" $current_time $rc
    total_time=$(echo "$total_time+$current_time" | bc)
    E2=$(echo "scale=3; $E2+$current_time^2" | bc)
  done

  mean=$(echo "scale=3; $total_time/$runs" | bc)
  mean2=$(echo "$mean^2" | bc)
  E2=$(echo "scale=3; $E2/$runs" | bc)
  std=$(echo "scale=3; sqrt($E2-$mean2)" | bc)

  if (( $threads == 1 )); then
    baseline=$mean
  fi

  printf "\t[ mean    = %8.3f ms ]\n" $mean
  printf "\t[ std     = %8.3f ms ]\n" $std
  if [[ -n $baseline ]]; then
    speedup=$(echo "scale=3; $baseline/$mean" | bc)
    printf "\t[ speedup = %8.2f    ]\n" $speedup
  fi
done

timer_stop=$(date +%s.%3N)
elapsed=$(echo "scale=3; $timer_stop-$timer_start" | bc)

echo
echo "\"$outfile\" is ready" 
echo "Elapsed time: $elapsed s"
echo
