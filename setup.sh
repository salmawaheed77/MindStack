#!/usr/bin/env bash
# MindStack setup script (Ubuntu). Run from the project root: bash setup.sh
set -e
cd "$(dirname "$0")"

echo "Installing system packages..."

sudo apt update

sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    ffmpeg \
    alsa-utils \
    pulseaudio-utils \
    build-essential \
    espeak-ng \
    libespeak-ng1

echo "Creating virtual environment..."

python3 -m venv venv

echo "Installing Python packages..."

venv/bin/pip install --upgrade pip

venv/bin/pip install -r requirements.txt

venv/bin/pip install \
    -r gui/mindstack_gui_english/mindstack_gui/requirements.txt
