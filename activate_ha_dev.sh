#!/usr/bin/env bash
#pip3 install yarl==1.8.1 awesomeversion==22.9.0
script/setup
source venv/bin/activate
hass -c config
