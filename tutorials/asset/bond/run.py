import sys
from cashflower import start
from tutorials.asset.bond.settings import settings

if __name__ == "__main__":
    output = start("tutorials.asset.bond", settings, sys.argv)
