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
    def __init__(self, task_name, cmdline, workunits, directory=None,line_filter=None, progress_hook=None, wu_failure_hook=None):
        self.task_name = task_name
        self.cmdline = cmdline
        self.workunit_names = workunits # WARNING: ASSUMED TO BE UNIQUE
        if directory==None:
            directory="tasks/%s/" % task_name
            if not os.path.isdir(directory):
                os.makedirs(directory)
        self.directory = directory
        self.line_filter = line_filter
        self.progress_hook = progress_hook
        self.wu_failure_hook = wu_failure_hook

    def all_workunits(self):
        for wu_name in map(str,self.workunit_names):
            yield Workunit(
                workunit_name=wu_name,
                cmdline = self.cmdline.replace("WORKUNIT", wu_name),
                task_dir = self.directory,
                line_filter=self.line_filter
                )

    def all_remaining_workunits(self):
        for wu in self.all_workunits():
            if not wu.is_done() and not wu.is_running():
                yield wu


    def execute(self):
        for wu in self.all_remaining_workunits():
            try:
                wu.execute()
                if self.progress_hook:
                    self.progress_hook(wu, self)
            except Exception:
                print "EXCEPTION!"
                exc_type, exc_value, exc_traceback = sys.exc_info()
                exc = traceback.format_exception(exc_type, exc_value,
                                                 exc_traceback,
                                                 file=sys.stderr)
                exc = "".join(exc)+"\nTask: %s\nWorkunit: %s"%(
                    self.task_name, wu.workunit_name)
                sys.stderr.write(exc)
                if self.wu_failure_hook:
                    self.wu_failure_hook(wu, exc, self)


#(self, task_name, cmdline, workunits, directory=None,line_filter=None, progress_hook=None, wu_failure_hook=None):
t = Task("test_task", "sleep 1; echo work WORKUNIT; sleep WORKUNIT;",
         xrange(25))
print "Running..."
t.execute()
