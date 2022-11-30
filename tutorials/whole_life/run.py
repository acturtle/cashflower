import sys

from cashflower import start
from tutorials.whole_life.settings import settings


if __name__ == "__main__":
    start("tutorials.whole_life", settings, sys.argv)
