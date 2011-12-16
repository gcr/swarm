#!/usr/bin/env python2
# -*- coding: utf-8
import argparse
import sys
from worker import WorkerPool

parser = argparse.ArgumentParser(description="Manage your running tasks.",
                                 epilog="One of --work or --report is required.")
parser.add_argument(
    '--work', '-w', action='store_true',
    help="Spawn a worker"
)

parser.add_argument(
    '--report', '-r', action='store_true',
    help="Report on the status of the experiment"
)

parser.add_argument(
    '--concurrency', '-c', nargs='?', default=1, type=int,
    help="How many workers to spawn"
)

parser.add_argument(
    '--tasks', '-t', nargs='+',
    help="Restrict to only the listed tasks"
)

def swarm(tasks,
          line_filter=None, progress_hook=None, wu_failure_hook=None):
    args = parser.parse_args()
    if args.tasks:
        tasks = [t for t in tasks if t.name in args.tasks]

    if args.work and not args.report:
        w = WorkerPool(tasks, args.concurrency, line_filter=line_filter,
                       progress_hook=progress_hook,
                       wu_failure_hook=wu_failure_hook)
        w.execute()
    elif args.report and not args.work:
        for task in tasks:
            report_task(task)
    else:
        parser.print_help()



def report_task(task):
    if task.is_done():
        print "\nTask %s done" % task.name
        return
    bar_width=50

    total,complete,running,todo=task.progress()
    print "\n-----"
    n="Task: %s" % task.name
    c="%.2f%%  %d/%d" % (float(complete)*100/total, complete,total)

    print n + " "*max(5, 2+bar_width-len(n)-len(c))+c
    # Draw an ASCII progress bar

    sys.stdout.write("[")
    for w in xrange(bar_width):
        i = w/float(bar_width) * total
        if i < complete:
            sys.stdout.write("=")
        elif complete <= i < (complete+running):
            sys.stdout.write(",")
        else:
            sys.stdout.write(".")
    sys.stdout.write("]\n")
    sys.stdout.flush()

    if running>0:
        s=0
        for wu in task.all_workunits():
            try:
                s += wu.time_finished()
            except Exception:
                pass
        if complete > 0 and s > 0:
            avg_wu_time = s / complete
            seconds = ((total-complete)*avg_wu_time) / running
            hours=minutes=0
            minutes = int(seconds/60)
            hours = int(minutes/60)
            print "ETA %02d:%02d:%02d" % (hours,minutes%60,seconds%60)

    # Who's working?
    print "Workers:",
    hosts = {}
    for wu in task.all_workunits():
        try:
            hostname = wu.which_host()
            hosts[hostname] = hosts.get(hostname,0)+1
        except Exception:
            pass
    print ", ".join([
            "%s x%s" % (hostname,count)
            for hostname,count in hosts.items()]),
    print " (%d total)" % running
