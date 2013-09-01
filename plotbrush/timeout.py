import multiprocessing
import time

def timeout(target, args=None, timeout=1):
    # Start foo as a process

    if args:
        p = multiprocessing.Process(target=target, name="Foo", args=args)
    else:
        p = multiprocessing.Process(target=target, name="Foo")

    p.start()

    # Wait 10 seconds for foo
    time.sleep(timeout)

    # Terminate foo
    p.terminate()

    # Cleanup
    p.join()
