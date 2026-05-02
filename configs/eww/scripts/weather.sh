#!/bin/bash
CITY="Guadalajara"

case $1 in
  temp)
    curl -s "wttr.in/$CITY?format=%t" | tr -d '+°C' | tr -d ' '
    ;;
  desc)
    curl -s "wttr.in/$CITY?format=%C"
    ;;
  icon)
    curl -s "wttr.in/$CITY?format=%c"
    ;;
  humidity)
    curl -s "wttr.in/$CITY?format=%h"
    ;;
  wind)
    curl -s "wttr.in/$CITY?format=%w"
    ;;
  full)
    curl -s "wttr.in/$CITY?format=%c+%t+%C"
    ;;
esac