import time

class Timer():
    @staticmethod
    def tic():
        global tictoc_start
        #tictoc_start = int(round(time.time() * 1000))
        tictoc_start = time.time()
        
    @staticmethod
    def toc(name):
        if 'tictoc_start' in globals():
            #print "Time delta (" + name + ")= " + str(int(round(time.time() * 1000)) - tictoc_start) + " ms"
            print "Time delta (" + name + ")= " + str(round(((time.time() - tictoc_start) * 1000),2)) + " ms"
        else:
            print "Toc: start time not set"
