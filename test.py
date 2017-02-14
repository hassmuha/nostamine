import threading

def worker(num,denum):
    """thread worker function"""
    print 'Worker: %s %s' % (num,denum)
    return

threads = []
for i in range(5):
    t = threading.Thread(target=worker, args=(i,"fdsf",))
    threads.append(t)
    t.start()
