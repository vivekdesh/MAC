#!/bin/bash

SCRIPT_DIR="/Users/vivek/icici_direct/mac"

echo "Executing to_google.sh (for Vivek) for mod_rsi..."
bash "$SCRIPT_DIR/to_google.sh" mod_rsi

echo "Executing ToAWS_suresh.sh..."
bash "$SCRIPT_DIR/ToAWS_suresh.sh"

echo "All scripts executed."
