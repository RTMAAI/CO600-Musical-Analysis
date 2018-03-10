#!/bin/sh
# Init script for Linux users

source venv/bin/activate

pip3 install -r requirements.txt

python3 example_implementation.py
