#!/usr/bin/env bash
set -e

echo "Installing marom_tool ..."
sudo yum install -y python3.11
python3 -m venv .venv
source .venv/bin/activate
curl -O https://bootstrap.pypa.io/get-pip.py
python3.11 get-pip.py
python3.11 -m pip install boto3

pip3.11 install --upgrade pip
pip3.11 install -r requirements.txt

echo "Setup complete."
echo "To start using:"
echo "source .venv/bin/activate"
echo "python3.11 maromtool.py --help"

