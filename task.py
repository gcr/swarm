#!/usr/bin/env python2
# -*- coding: utf-8

from workunit import Workunit
import os
import traceback
import sys

class Task(object):
    """
    A task is merely a collection of workunits.

    Tasks have:
    - A name
    - A command line
    - A task directory
    - N workunit names, spliced to the commandline
    """
    def __init__(self, name, cmdline, workunits, directory=None,line_filter=None):
        self.name = name
        self.cmdline = cmdline
        self.workunit_names = workunits # WARNING: ASSUMED TO BE UNIQUE
        if directory==None:
            directory="tasks/%s/" % name
            if not os.path.isdir(directory):
                os.makedirs(directory)
        self.directory = directory
        self.line_filter = line_filter

    def all_workunits(self):
        for wu_name in map(str,self.workunit_names):
            yield Workunit(
                name=wu_name,
                cmdline = self.cmdline.replace("WORKUNIT", wu_name),
                task_dir = self.directory,
                line_filter=self.line_filter
                )

    def all_remaining_workunits(self):
        for wu in self.all_workunits():
            if not wu.is_done() and not wu.is_running():
                yield wu

    def is_done(self):
        return all([ wu.is_done()
                     for wu in self.all_workunits()])

    def progress(self):
        total = complete = running = todo = 0
        for wu in self.all_workunits():
            total += 1
            if wu.is_done():
                complete += 1
            elif wu.is_running():
                running += 1
            else:
                todo += 1
        return total,complete,running,todo


    def execute(self,progress_hook=None,wu_failure_hook=None):
        """
        Perform every unfinished workunit in this task.
        Make multiple passes until there's no more work left.
        """
        another_pass = True
        while another_pass:
            another_pass = False
            for wu in self.all_remaining_workunits():
                try:
                    wu.execute()
                    another_pass = True
                    if progress_hook:
                        progress_hook(wu, self)
                except Exception:
                    print "EXCEPTION!"
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    exc = traceback.format_exception(exc_type, exc_value,
                                                     exc_traceback)
                    exc = "".join(exc)+"\nTask: %s\nWorkunit: %s"%(
                        self.name, wu.name)
                    sys.stderr.write(exc)
                    if wu_failure_hook:
                        wu_failure_hook(wu, exc, self)


# t = Task("test_task", "sleep 1; echo work WORKUNIT; sleep WORKUNIT;",
#          xrange(25))
# print "Running..."
# t.execute()
