import sys
from cashflower import start
from settings import settings


if __name__ == "__main__":
    start("temporary", settings, sys.argv)
