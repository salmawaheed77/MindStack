#!/usr/bin/env bash
# MindStack setup script (Ubuntu). Run from the project root: bash setup.sh
set -e
cd "$(dirname "$0")"

echo "Installing system packages..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git alsa-utils pulseaudio-utils build-essential

echo "Creating virtual environment..."
python3 -m venv venv

echo "Installing Python packages..."
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

echo "Checking microphone..."
arecord -l || echo "No recording device found. See docs/SETUP.md (Microphone section)."

echo ""
echo "Done. Activate the environment with: source venv/bin/activate"
