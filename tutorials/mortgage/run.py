import sys
from cashflower import start
from tutorials.mortgage.settings import settings

if __name__ == "__main__":
    output = start("tutorials.mortgage", settings, sys.argv)
