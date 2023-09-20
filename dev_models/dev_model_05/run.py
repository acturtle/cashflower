import sys
from cashflower import start
from settings import settings


if __name__ == "__main__":
    output = start(settings, sys.argv)
