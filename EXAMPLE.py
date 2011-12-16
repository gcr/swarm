#!/usr/bin/env python2
# -*- coding: utf-8
from swarm import swarm
from task import Task

swarm(
    tasks=[
        Task("test_task",
             cmdline="sleep 5; echo XXX; echo work WORKUNIT;",
             workunits=xrange(25)),
        Task("test_task2",
             cmdline="sleep 10; echo work2 WORKUNIT;",
             workunits=xrange(25))
        ],
    line_filter = lambda line: line.strip() == "XXX"
    )
