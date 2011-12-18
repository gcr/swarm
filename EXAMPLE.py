#!/usr/bin/env python2
# -*- coding: utf-8
from swarm import swarm, Task
import os

INPUT_VIDEOS = os.listdir("input")

swarm(
    tasks=[

        Task("convert_to_avi",
             cmdline="ffmpeg -i input/WORKUNIT -vcodec msmpeg4v2 output-WORKUNIT.avi",
             workunits=INPUT_VIDEOS),

        Task("convert_to_mp4",
             cmdline="ffmpeg -i input/WORKUNIT -vcodec mpeg4 output-WORKUNIT.mp4",
             workunits=INPUT_VIDEOS),

        Task("rip_sound",
             cmdline="ffmpeg -i input/WORKUNIT output-WORKUNIT.ogg",
             workunits=INPUT_VIDEOS),

        ]
    )
