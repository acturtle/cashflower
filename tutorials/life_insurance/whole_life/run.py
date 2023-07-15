import sys
from cashflower import start
from settings import settings


if __name__ == "__main__":
    output = start("whole_life", settings, sys.argv)
