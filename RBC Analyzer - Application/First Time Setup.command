#!/bin/zsh
cd -- "${0:A:h}" || exit 1
if command -v python3 >/dev/null 2>&1; then
  python3 app/install_rbc.py
  result=$?
else
  print 'Install Python 3.10+ from https://www.python.org/downloads/ then run this file again.'
  result=1
fi
printf '\nPress Return to close.'
read -r reply
exit "$result"
