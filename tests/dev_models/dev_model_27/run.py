import os
from cashflower import run
from settings import settings  # Import settings from the settings.py file


# Main entry point for running the model
if __name__ == "__main__":
    output, diagnostic, log = run(settings=settings, path=os.path.dirname(__file__))
