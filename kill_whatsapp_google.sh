#!/bin/bash

USER_HOME=$(eval echo "~$USER")
bash "$USER_HOME/whatsapp/kill_whatsapp_google.sh" "$@"
