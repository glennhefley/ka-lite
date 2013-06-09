import threading, subprocess
from croncount import get_count
import gc

def cron():
    import pdb; pdb.set_trace()
    # only bother spinning up the full cron management command if there's something waiting to be run
    if get_count():
        subprocess.call(["python", "manage.py", "cron"])
    gc.set_debug(gc.DEBUG_LEAK or gc.DEBUG_STATS or gc.DEBUG_UNCOLLECTABLE or gc.DEBUG_INSTANCES or gc.DEBUG_OBJECTS)
    import pdb; pdb.set_trace()
    gc.collect()
    threading.Timer(5, cron).start()

if __name__ == "__main__":
    gc.set_debug(gc.DEBUG_LEAK or gc.DEBUG_STATS or gc.DEBUG_UNCOLLECTABLE or gc.DEBUG_INSTANCES or gc.DEBUG_OBJECTS)
    cron()
