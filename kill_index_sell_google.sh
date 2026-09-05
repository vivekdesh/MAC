#!/bin/bash

# Thin shim: sync_master.sh uploads MAC/kill_*.sh to the VM's home directory, and this
# forwards to the real script inside the bot folder. Mirrors kill_selling_google.sh.
bash /home/deshpande_vivek/sell_index/kill_index_sell.sh "$@"
