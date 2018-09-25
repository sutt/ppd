import time

#https://github.com/Microsoft/ptvsd/issues/837

def basic():

    i=0
    t0 = time.time()

    while(True):
        i += 1
        if i % 10**6 == 0:
            print str(time.time() - t0)[:4]
            t0 = time.time()
            i = 0

if __name__ == "__main__":
    basic()