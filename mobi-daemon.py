#!/home/msj/miniconda3/bin/python3

import sys
from daemoner import Daemon, log
import twitterer
from mobitools import *
import time
import datetime
import random
import os

def g():
    twitterer.warning("@vanbikesharebot is shutting down")
    pass

def pick_tweet_hour():
    hours = list(range(8,15))
    return random.choice(hours)

def f(workingdir):
    log(workingdir)
    workingdir = os.path.abspath(workingdir)
    log(workingdir)
    cycles = 0
    hour = datetime.datetime.now().hour
    day = datetime.datetime.now().day
    tweettime = -1 # avoid double tweeting if you restart the daemon
    
    while True:
        
        ## Once a day, pick the hour for summary tweet to be sent
        if day != datetime.datetime.now().day:
            tweettime = pick_tweet_hour()
            log(f"Today's tweet will be at: {tweettime}")
            day = datetime.datetime.now().day
            
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
            
            if hour == tweettime:
                try:
                    s,ims = daily_summary(workingdir)
                    log(s)
                    log(ims)
                    twitterer.tweet('VanBikeShareBot',s,ims)
                except Exception as e:
                    twitterer.warning("Daily @vanbikesharebot tweet failed")
                    log(e)
        log("Querying mobi....")
        query(workingdir)
        
        cycles += 1
        time.sleep(60)

        
fkwargs = {'workingdir':'./'}
d = Daemon(f=f,fkwargs=fkwargs,pidfilename='./daemon.pid',g=g)
d.run()
