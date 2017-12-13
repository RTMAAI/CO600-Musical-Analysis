#!/bin/sh
# Init script for Linux/Mac users

source venv/bin/activate

pip install -r requirements.txt

python example_implementation.py