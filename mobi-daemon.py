#!/home/msj/miniconda3/bin/python3

import sys
from daemoner import Daemon, log
import twitterer
from mobitools import *
import time
import datetime
import random
import os

logfile='mobi-daemon.log'

def g():
    twitterer.warning("@vanbikesharebot is shutting down")
    pass

def pick_tweet_hour():
    hours = list(range(8,15))
    return random.choice(hours)

def f(workingdir):
    log('v2',file=logfile)
    log(workingdir,file=logfile)
    workingdir = os.path.abspath(workingdir)
    log(workingdir,file=logfile)
    cycles = 0
    hour = datetime.datetime.now().hour
    day = datetime.datetime.now().day
    tweettime = -1 # avoid double tweeting if you restart the daemon
    
    while True:
        
        ## Once a day, pick the hour for summary tweet to be sent
        if day != datetime.datetime.now().day:
            tweettime = pick_tweet_hour()
            log(f"Today's tweet will be at: {tweettime}",file=logfile)
            twitterer.warning(f"Today's @vanbikesharebot tweet will be at: {tweettime}")
            day = datetime.datetime.now().day
            
        ## Once an hour, update CSV files and make plots
        if hour != datetime.datetime.now().hour:
            
            ## Update CSV files (taken_daily_df.csv)
            log("Updating CSV files",file=logfile)
            try:
                update_csv(workingdir)
            except:
                log("update_csv failed")
            try:
                query(workingdir)  # This is necessary to create the daily dataframe which is needed to create plots (fix this)
            except:
                log("query failed")
            
            log("Drawing plots",file=logfile)
            try:
                draw_plots(workingdir)
                log("Finished plots",file=logfile)
            except Exception as e:
                log("draw_plots() failed due to the following exception:",file=logfile)
                log(e,file=logfile)
                
            try:
                query(workingdir)
                log("Updating stations",file=logfile)
            except:
                log("query failed")
            
            try:
                update_stations(workingdir)
            except Exception as e:
                log("Update stations filed due to the following exception:",file=logfile)
                log(e,file=logfile)
                    
                
            # Reset hour to current hour
            hour = datetime.datetime.now().hour
            
            if hour == tweettime:
                try:
                    s,ims = daily_summary(workingdir)
                    log(s,file=logfile)
                    log(ims,file=logfile)
                    twitterer.tweet('VanBikeShareBot',s,ims)
                except Exception as e:
                    twitterer.warning("Daily @vanbikesharebot tweet failed")
                    log(e,file=logfile)
                    
        try:
            log("Querying mobi....",file=logfile)
            query(workingdir)
        except:
            log("Query failed")
        cycles += 1
        time.sleep(60)

        
fkwargs = {'workingdir':'./'}
d = Daemon(f=f,fkwargs=fkwargs,pidfilename='./daemon.pid',g=g)
d.run()
