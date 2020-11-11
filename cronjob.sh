#!/bin/bash -l

echo $HOME
echo $SLACK_API_TOKEN
cd ~/pyprojs/nvscrape
source ~/.virtualenvs/pyprojsenv/bin/activate
python nvscrape.py
