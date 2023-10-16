import os
from cashflower import start
from settings import settings

if __name__ == "__main__":
    output = start(settings=settings, path=os.path.dirname(__file__))
