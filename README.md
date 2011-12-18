Swarm
=====

Swarm is a small Python library to distribute/parallelize long-running
command lines across many cores/many machines. I use this in my
research work to turn 10-day-long experiments into overnight
experiments.

Features
--------

- Distribute long-running jobs across many cores

- One machine not enough? Share the workload across many NFS-mounted
  (or SSHFS-mounted) machines for massive speed gains

- If things crash, swarm restarts your task roughly where you left off
  so you don't have to start the entire job from scratch

- Simple to use -- each task is just a command line. Just clone this
  repo, write a short script, and you're off!

- Lightweight and non-intrusive -- swarm keeps all of your jobs'
  stdout files and its internal lock files in a single 'tasks' folder.
  Just delete it to start over.

Quick Start
-----------

Split your work into one or more independent tasks. Each task is just
a command line. You can have many tasks that each run slightly
different command lines.

Split each task into workunits. Each workunit is the smallest possible
atomic computation; a single invocation of that task's command line,
changing only workunit flags for each invocation.

For example, suppose you want to convert lots of videos to many
different formats. In this case, each workunit would be the filename
of your input video file. You might have several tasks with several
command lines:

- `ffmpeg -i WORKUNIT -vcodec msmpeg4v2  output-WORKUNIT.avi`
- `ffmpeg -i WORKUNIT -vcodec h264 output-WORKUNIT.mp4`
- `ffmpeg -i WORKUNIT output-WORKUNIT.ogg`

Writing the swarm script
------------------------

This script describes each task and the list of workunits for each
task. Here's an example that will convert all of the videos in the
`input` folder to avi, mp4, and ogg:

    #!/usr/bin/env python2
    # -*- coding: utf-8
    #
    # video-convert.py
    #
    from swarm import swarm, Task
    import os

    INPUT_VIDEOS = os.listdir("input")

    swarm(tasks=[

            Task("convert_to_avi",
                 cmdline="ffmpeg -i input/WORKUNIT -vcodec msmpeg4v2 output-WORKUNIT.avi",
                 workunits=INPUT_VIDEOS),

            Task("convert_to_mp4",
                 cmdline="ffmpeg -i input/WORKUNIT -vcodec mpeg4 output-WORKUNIT.mp4",
                 workunits=INPUT_VIDEOS),

            Task("rip_sound",
                 cmdline="ffmpeg -i input/WORKUNIT output-WORKUNIT.ogg",
                 workunits=INPUT_VIDEOS),

          ])

Running your tasks
------------------

To begin converting your videos, run your swarm script:

    python video-convert.py --work --concurrency 2

This command will run two workunits at once on your computer; great if
you have a dual-core box.

Monitoring progress
-------------------

To get pretty reports, use the `--report` flag:

    $ python video-convert.py --report

    -----
    Task: convert_to_avi                     5.26%  2/38
    [===,,,............................................]
    ETA 1h 56m 21s
    Workers: localhost x2  (2 total)

    -----
    Task: convert_to_mp4                     0.00%  0/38
    [..................................................]
    Workers:   (0 total)

    -----
    Task: rip_sound                          0.00%  0/38
    [..................................................]
    Workers:   (0 total)

Our video conversion is well on its way!

If you want to get some details about each active workunit, use the
`--report-active` flag:

    $ python video-convert.py --report-active

    localhost  convert_to_avi / freeman_s_mind_episode_10.wmv
      Started:  57s ago
      Activity: 1s ago

    localhost  convert_to_avi / freeman_s_mind_episode_26.wmv
      Started:  46s ago
      Activity: 0s ago

This view shows you the current active workunits -- which host is
running which task and the name of the current workunit. `Started` is
how long this workunit has been running for and `Activity` is how long
ago the job last wrote a line to its stdout. This is great for finding
stuck/crashed workunits (see below).

Distributing the work
---------------------

You've already seen the `--concurrency` flag which lets you run
multiple workers on a single machine, but Swarm is smart enough to
share the workload across several machines. To use this, mount your
folder on a shared filesystem like NFS or SSHFS, then just run your
swarm script as usual. Swarm will then process the next unclaimed
workunits, taking (some) care not to clobber other machines' work.

Note that workunit locking works by passing the `O_EXCL` flag to
`open(2)`, which only works on certain Linux kernels and certain
versions of NFS. I don't think I have it right, so this may not be
very reliable. Worst case is that >1 one computer will perform the
same workunit and one's output will clobber the other.

The reporter prints the hostname for each active workunit so you can
see which machine is doing what.

Recovering from crashes
-----------------------

If an active workunit dies, swarm will pick up roughly where it left
off the next time you run your swarm script. Ideally, you'll lose only
that active workunit -- no need to start the entire task over.

Internally, swarm keeps a `tasks` folder with several workunit status
files plus a log of each workunit's standard out. If a workunit dies
and swarm perpetually thinks it's "active", remove the proper
`WORKUNIT.running` file from the `tasks` folder. If any workers are
running, one of them will eventually notice the incomplete workunit
and will simply start it again.

Map reduce
----------

Swarm implements the "map" step of the "map/reduce" algorithm. It's
not hard to run a "reduce" step -- just write a script that collects
all the stdout logs inside the tasks folder.
