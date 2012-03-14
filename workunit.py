#!/usr/bin/env python2
# -*- coding: utf-8

import os
import fcntl
import socket
import subprocess
import time
import atexit
import signal

class Workunit(object):
    def __init__(self, name, cmdline, task_dir, line_filter=None):
        self.name = name
        self.cmdline = cmdline
        self.task_dir = task_dir
        self.line_filter = line_filter

        self.lockfile = os.path.join(task_dir, name.replace("/","-")+".running")
        self.donefile = os.path.join(task_dir, name.replace("/","-")+".done")
        self.logfile = os.path.join(task_dir, name.replace("/","-")+".log")

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

    def time_started(self):
        """
        Returns unix time when the workunit was started
        """
        return os.stat(self.lockfile).st_ctime

    def time_last_activity(self):
        """
        Returns unix time when the workunit was last touched (line in
        the logfile)
        """
        return os.stat(self.logfile).st_mtime

    def duration(self):
        """
        Report how LONG this workunit took to finish
        """
        assert self.is_done()
        with open(self.donefile) as f:
            return float(f.read().strip())

    def execute(self):
        assert not self.is_done()
        start = time.time()
        # Acquire lock
        fd = os.open(self.lockfile, os.O_CREAT|os.O_EXCL|os.O_RDWR)
        os.close(fd)
        # passing O_EXCL is only safe for some NFS clients:
        # NFSv3, kernel 2.6.5 or better.
        # http://stackoverflow.com/questions/3406712/open-o-creat-o-excl-on-nfs-in-linux

        with open(self.lockfile, "w") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            f.write(socket.gethostname()+"\n")
            f.flush()

            with open(self.logfile, "w") as log:
                # Run process
                def session():
                    signal.signal(signal.SIGINT,signal.SIG_IGN)
                p = subprocess.Popen(
                    self.cmdline, shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    preexec_fn=session)
                # (Don't forward signals)

                # Kill this process when we die
                def killer(self,p):
                    if p.returncode == None:
                        # NOTE that the forked python dies with the
                        # child process
                        os.killpg(os.getpgid(p.pid),signal.SIGTERM)
                atexit.register(killer,self, p)

                # Process lines
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
