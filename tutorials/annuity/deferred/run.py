import sys

from cashflower import start
from tutorials.annuity.deferred.settings import settings


if __name__ == "__main__":
    start("deferred", settings, sys.argv)
