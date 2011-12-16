#!/usr/bin/env python2
# -*- coding: utf-8

import threading
import random
import time

class WorkerPool(object):
    """
    A pool of workers, each running one or more tasks.
    """
    def __init__(self,tasks, concurrency=2,
                 line_filter=None,
                 progress_hook=None,
                 wu_failure_hook=None):
        self.tasks = tasks
        self.concurrency = concurrency
        self.progress_hook=progress_hook
        self.wu_failure_hook=wu_failure_hook
        if line_filter is not None:
            # Override it in all our tasks!
            # todo: this is stupid stupid dumb
            for t in self.tasks:
                t.line_filter=line_filter

        assert len(set([t.name for t in tasks])) == len(tasks), "Some tasks have duplicate names!"

    def execute(self):
        threads = [
                threading.Thread(target=self.worker, args=(x,))
                for x in xrange(self.concurrency)
                ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def worker(self,worker_id):
        def progress_hook(wu,task):
            print "Worker %d finished %s / %s" % (
                worker_id, task.name, wu.name)
            if self.progress_hook:
                self.progress_hook(wu,task)
        def wu_failure_hook(wu, message, task):
            print "Worker %d failed task %s / %s\n%s" % (
                worker_id, task.name, wu.name, message)
            if self.wu_failure_hook:
                self.wu_failure_hook(wu,message,task)

        print "Starting worker %d" % worker_id
        time.sleep(random.random())
        for task in self.tasks:
            print "Worker %d working on task %s" % (worker_id,task.name)
            task.execute(progress_hook=progress_hook,wu_failure_hook=wu_failure_hook)
        print "Worker %d has nothing left to do" % worker_id


# from task import Task
# w = WorkerPool(
#     tasks=[
#         Task("test_task", "sleep 1; echo work WORKUNIT; sleep WORKUNIT;",
#              xrange(25)),
#         Task("test_task2", "sleep 10; echo work2 WORKUNIT; sleep WORKUNIT;",
#              xrange(25))
#         ],
#     concurrency=25
#     )
# w.execute()
