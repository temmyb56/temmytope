#!/usr/bin/python3
import sys
import os

# Add your project directory to sys.path
sys.path.insert(0, '/home/yourusername/army-ticket-generator/')

from backend import app as application

if __name__ == "__main__":
    application.run()