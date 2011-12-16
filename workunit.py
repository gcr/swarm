#!/usr/bin/env python2
# -*- coding: utf-8

import os
import fcntl
import socket
import subprocess
import time

class Workunit(object):
    def __init__(self, name, cmdline, task_dir, line_filter=None):
        self.name = name
        self.cmdline = cmdline
        self.task_dir = task_dir
        self.line_filter = line_filter

        self.lockfile = os.path.join(task_dir, name+".running")
        self.donefile = os.path.join(task_dir, name+".done")
        self.logfile = os.path.join(task_dir, name+".log")

    def is_running(self):
        return os.path.isfile(self.lockfile)

    def is_done(self):
        return os.path.isfile(self.donefile)

    def which_host(self):
        assert self.is_running()
        with open(self.lockfile) as f:
            host = f.read().strip()
        if host == '':
            time.sleep(0.1)
            return self.which_host()
        else:
            return host

    def time_finished(self):
        assert self.is_done()
        with open(self.donefile) as f:
            return float(f.read().strip())

    def execute(self):
        assert not self.is_done()
        start = time.time()
        # Acquire lock
        fd = os.open(self.lockfile, os.O_CREAT|os.O_EXCL|os.O_RDWR)
        os.close(fd)
        # passing O_EXCL works for some NFS clients

        with open(self.lockfile, "w") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            f.write(socket.gethostname()+"\n")
            f.flush()

            with open(self.logfile, "w") as log:
                # Run process
                p = subprocess.Popen(self.cmdline, shell=True,
                                     stdout=subprocess.PIPE)
                for line in iter(p.stdout.readline, ''):
                    if (not self.line_filter
                        or (self.line_filter and self.line_filter(line))):
                        log.write(line)
                        log.flush()

                p.wait()
                if p.returncode != 0:
                    # Note that the lockfile will still be there. I think
                    # this is a good thing.
                    raise IOError("Process returned exit code %d; command line was %s" % (
                            p.returncode, self.cmdline))

            fcntl.flock(f, fcntl.LOCK_UN)

        # Release lock
        with open(self.donefile, "w") as f:
            f.write("%f\n" % (time.time() - start))

        os.remove(self.lockfile)

#w = Workunit("Foo", "sleep 5; echo 'Hi'; sleep 5; echo 'Bye'; sleep 5; exit 0", "/tmp/workunit-test")
#w.execute()
