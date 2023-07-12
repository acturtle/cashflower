import sys
from cashflower import start
from tutorials.life_insurance.whole_life.settings import settings

if __name__ == "__main__":
    output = start("tutorials.life_insurance.whole_life", settings, sys.argv)
