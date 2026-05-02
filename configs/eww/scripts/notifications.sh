#!/bin/bash
case $1 in
  get)
    dunstctl history | python3 -c "
import sys, json
data = json.load(sys.stdin)
notifs = data.get('data', [[]])[0][:5]
for n in notifs:
    summary = n.get('summary', {}).get('data', 'No title')
    body = n.get('body', {}).get('data', '')[:40]
    print(f'{summary}|{body}')
" 2>/dev/null || echo "Sin notificaciones|"
    ;;
  clear)
    dunstctl history-clear
    ;;
esac