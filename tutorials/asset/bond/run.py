import sys
from cashflower import start
from settings import settings


if __name__ == "__main__":
    output = start("bond", settings, sys.argv)
