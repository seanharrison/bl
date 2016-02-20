
import os, sys, subprocess, time, traceback, random, tempfile
from glob import glob
from bl.dict import Dict
from bl.text import Text

"""There are other queue libraries; this one implements a simple file-based queue 
that is processed at set intervals by the queue process. 
JSON is the default queue entry data extension, processed according to the specs of the subclass.
Queue entry data is passed to the process_entry() method as bytes.
If there is one queue process, it is a synchronous queue -- entries are processed FIFO.
If there are multiple queue processes, it is asynchronous -- each process is synchronous, 
but there is no synchronization between the processes; each process picks up the next entry.
"""

class Queue(Dict):

    def __init__(self, path, outpath=None, log=print, debug=False, **args):
        if not os.path.exists(path): os.makedirs(path)
        if outpath is None: outpath = path + '.OUT'
        if not os.path.exists(outpath): os.makedirs(outpath)
        Dict.__init__(self, path=path, outpath=outpath, log=log, debug=debug, **args)
        self.log("[%s] init %r" % (self.timestamp(), self.__class__))

    def __repr__(self):
        return "%s(path='%s')" % (self.__class__.__name__, self.path)

    def timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S %Z")

    def listen(self, sleep=5):
        """listen to the queue directory, with a wait time in seconds between processing"""
        while True:
            self.process_queue()
            time.sleep(sleep)

    def insert(self, text, prefix="", suffix="", ext='.json'):
        """insert the given queue entry into the queue.
        text    : the text of the queue entry (REQUIRED)
        prefix  : a prefix for each queue entry filename (default '')
        suffix  : a suffix for each queue entry filename (before extension, default '')
        ext     : the extension of the queue entry filename (default '.json') 
        """
        qfn = os.path.join(self.path, "%s%s-%.5f%s%s" 
            % (prefix, time.strftime("%Y%m%d.%H%M%S.%f"), random.random(), suffix, ext))
        qf = Text(fn=qfn, text=text)
        qf.write()
        return qfn

    def list(self, pattern="*"):
        """get a list of files currently in the queue, sorted in order."""
        l = [fn 
            for fn in glob(os.path.join(self.path, pattern))
            if not os.path.isdir(fn)]
        l.sort()
        return l

    def process_queue(self):
        """Loop through all the currently-available queue entry files, in order; 
        For each file, 
            + read it, delete it (to prevent another process from reading), then process it
            + if an exception happens processing an entry, log it and continue to the next item
        """
        fns = self.list()
        for fn in fns:
            self.log("[%s] %s" % (self.timestamp(), fn))

            # ensure that another queue process has not and will not process this entry.
            try:
                newfn = os.path.join(outpath, os.path.basename(fn))
                os.rename(fn, newfn)
            except:
                self.log("-- doesn't exist; already processed")
                continue

            # process this entry
            try:
                self.process_entry(newfn)
            except exception:
                self.handle_exception(fn=fn, exception=exception)

    def process_entry(self, fn):
        """override this method to define how your subclass queue processes entries.
        fn      : the filename of the queue entry, which is probably in self.outpath
        """
        self.log("process_entry():", fn)

    def handle_exception(self, fn=None, exception=exception):
        """Handle exceptions that occur during queue script execution.
        (Override this method to implement your own exception handling.)
        fn          : the filename of the queue entry.
        exception   : the exception object
        """
        self.log("== EXCEPTION:", fn)
        self.log(traceback.format_exc())

