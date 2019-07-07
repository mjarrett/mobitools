#!/home/msj/miniconda3/bin/python3

import sys
sys.path.append('/home/msj/daemon/')
from daemon import Daemon, log
sys.path.append('/home/msj/twitter/')
import twitter
from mobitools import *
import time
import datetime

import os

def g():
    twitter.warning("@vanbikesharebot is shutting down")

def f(workingdir):
    log(workingdir)
    workingdir = os.path.abspath(workingdir)
    log(workingdir)
    cycles = 0
    hour = datetime.datetime.now().hour
    while True:
        ## Once an hour, update CSV files and make plots
        if hour != datetime.datetime.now().hour:
            
            ## Update CSV files (taken_daily_df.csv)
            log("Updating CSV files")
            update_csv(workingdir)
            query(workingdir)  # This is necessary to create the daily dataframe which is needed to create plots (fix this)
            
            
            log("Drawing plots")
            try:
                draw_plots(workingdir)
                log("Finished plots")
            except Exception as e:
                log("draw_plots() failed due to the following exception:")
                log(e)
                
            
            
            log("Updating stations")
            update_stations(workingdir)
            
            # Reset hour to current hour
            hour = datetime.datetime.now().hour
            
            if hour == 12:
                try:
                    daily_summary(workingdir)
                except Exception as e:
                    twitter.warning("Daily @vanbikesharebot tweet failed")
                    log(e)
        log("Querying mobi....")
        query(workingdir)
        
        cycles += 1
        time.sleep(60)

        
fkwargs = {'workingdir':'./'}
d = Daemon(f=f,fkwargs=fkwargs,pidfilename='./daemon.pid',g=g)
d.run()
