#!/bin/zsh
# Reproduce and count the display flicker, so a fix can be judged with numbers instead of by eye.
#
# It opens and quits a few stock apps in a loop (opening apps is what triggers the flicker), then reads the
# system log and counts two events:
#   drops      a display falling to "1 x 1" and coming back, as logged by the graphics policy driver
#   reconfigs  WindowServer reconfiguring all displays, which is the flicker you see
#
# Usage: tools/measure-flicker.sh [loops]     (default: 4 loops, about 30 seconds each)
#
# Apps that are already running when you start are left alone, so no unsaved work is ever closed.
# Note for zsh users: `log` is a shell builtin, hence the full path below.

loops=${1:-4}
apps=(Calculator TextEdit Notes "System Settings" Safari "Activity Monitor")

if ! [[ $loops == <-> ]] || (( loops < 1 )); then
  echo "usage: $0 [loops]  (loops must be a positive number)" >&2
  exit 2
fi

skip=()
for app in $apps; do
  if [[ $(osascript -e "application \"$app\" is running" 2>/dev/null) == true ]]; then
    skip+=("$app")
    echo "skipping $app: it is already running, and it will not be touched" >&2
  fi
done

start=$(date '+%Y-%m-%d %H:%M:%S')
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

for (( i = 1; i <= loops; i++ )); do
  for app in $apps; do
    (( ${skip[(Ie)$app]} )) && continue
    open -a "$app" 2>/dev/null
    sleep 4
    osascript -e "tell application \"$app\" to quit" 2>/dev/null
    sleep 1
  done
done
sleep 4

/usr/bin/log show --start "$start" --style compact \
  --predicate 'process == "kernel" OR process == "WindowServer"' 2>/dev/null > "$tmp"

drops=$(grep -E 'FB:[0-9]+ -> 1 x 1' "$tmp" | awk '{print substr($2,1,8)}' | uniq | wc -l | tr -d ' ')
reconfigs=$(grep -c 'Reconfiguration started' "$tmp" | tr -d ' ')

echo "loops=$loops drops=$drops reconfigs=$reconfigs"
