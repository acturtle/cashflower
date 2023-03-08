import sys
from functools import partial
from multiprocessing import cpu_count, Pool
from cashflower import execute, merge_and_save, start
from tutorials.life_insurance.whole_life.settings import settings


if __name__ == "__main__":
    model_name = "tutorials.life_insurance.whole_life"

    if settings.get("MULTIPROCESSING"):
        cpu_count = cpu_count()
        p = partial(execute, model_name=model_name, settings=settings, cpu_count=cpu_count, argv=sys.argv)
        with Pool(cpu_count) as pool:
            outputs = pool.map(p, range(cpu_count))
        merge_and_save(outputs, settings)
    else:
        start(model_name, settings, sys.argv)
