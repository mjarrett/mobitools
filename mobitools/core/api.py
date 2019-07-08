import os
import sys
import signal
import time
from matplotlib import pyplot as plt
import pandas as pd
from pandas.io.json import json_normalize
import json
import urllib
import datetime
from mobitools.core.helpers import *
from mobitools.plots.plots import *



def breakdown_ddf(dailydf,workingdir='./'):

    """
    Takes as input input the dataframe created by
    running "query_mobi_api.py" N number of
    times.

    Returns dataframes with the number of bikes
    taken, returned and both, respectively, at
    each query
    """


    # Make pivot table from daily df
    pdf = pd.pivot_table(dailydf,columns='name',index='time',values='avl_bikes')
    pdf.index = pd.to_datetime(pdf.index)
    ddf = pdf.copy()

    for col in pdf.columns:
        ddf[col] = pdf[col] - pdf[col].shift(-1)

    takendf = ddf.fillna(0.0).astype(int)
    returneddf = ddf.fillna(0.0).astype(int)

    takendf[takendf>0] = 0
    returneddf[returneddf<0] = 0

    takendf = takendf*-1

    return takendf, returneddf

def update_dataframes(takendf, returneddf,workingdir='./'):

    """
    Takes as input the dataframes created by "breakdown_ddf()"
    Groups by hour and day to create summary dataframes. Appends
    to existing csv if extant, otherwise creates
    new csv
    """



    try:
        taken_hourly_df = pd.read_csv('{}/taken_hourly_df.csv'.format(workingdir),index_col=0)
        taken_hourly_df.index = pd.to_datetime(taken_hourly_df.index)

    except:
        taken_hourly_df = pd.DataFrame()


    taken_hourly_df = pd.concat([taken_hourly_df,takendf.groupby(pd.Grouper(freq='H')).sum()],sort=True)
    taken_hourly_df = taken_hourly_df.groupby(taken_hourly_df.index).sum()
    taken_hourly_df.to_csv('{}/taken_hourly_df.csv'.format(workingdir))


    try:
        returned_hourly_df = pd.read_csv('{}/returned_hourly_df.csv'.format(workingdir),index_col=0)
        returned_hourly_df.index = pd.to_datetime(returned_hourly_df.index)
    except:
        returned_hourly_df = pd.DataFrame()

    returned_hourly_df = pd.concat([returned_hourly_df,returneddf.groupby(pd.Grouper(freq='H')).sum()],sort=True)
    returned_hourly_df = returned_hourly_df.groupby(returned_hourly_df.index).sum()
    returned_hourly_df.to_csv('{}/returned_hourly_df.csv'.format(workingdir))


def update_csv(workingdir):
     ## Update CSV files (taken_daily_df.csv)
    update_stations_df(workingdir)

    # Load daily dataframe
    dailydf = pd.read_csv('{}/daily_mobi_dataframe.csv'.format(workingdir))
    a,b = breakdown_ddf(dailydf)
    update_dataframes(a,b,workingdir=workingdir)

    # Rename daily df
    timestr = time.strftime("%Y%m%d-%H%M%S")

    try:
        os.mkdir('{}/backups/'.format(workingdir))
    except:
        pass
    os.rename('{}/daily_mobi_dataframe.csv'.format(workingdir),
              '{}/backups/daily_mobi_dataframe.csv_BAK_{}'.format(workingdir,timestr))
    
def query(workingdir):
    daily_df = '{}/daily_mobi_dataframe.csv'.format(workingdir)

    # Query mobi API. If query fails, continue
    try:
        with urllib.request.urlopen("http://vancouver-ca.smoove.pro/api-public/stations") as url:
            data = json.loads(url.read().decode())
    except:
        return False
    # Try to load daily df. If it doesn't exist, create it. Append newly queried data to the end of it.
    try:
        df = pd.read_csv(daily_df)
    except:
        df = pd.DataFrame()

    newdf = json_normalize(data['result'])
    newdf['time'] = datetime.datetime.now()
    newdf['id'],newdf['name'] = newdf['name'].str.split(' ', 1).str

    df = df.append(newdf,ignore_index=True)
    df.to_csv(daily_df,index=False)
    del df
    return True

def draw_plots(workingdir):

    thdf = load_csv(f'{workingdir}/taken_hourly_df.csv')
    tddf = thdf.groupby(pd.Grouper(freq='d')).sum()

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    thisyear = datetime.datetime.now().strftime('%Y')
    yday = (datetime.datetime.now() - datetime.timedelta(1)).strftime('%Y-%m-%d')
    yday_min7 = (datetime.datetime.now() - datetime.timedelta(8)).strftime('%Y-%m-%d')
    yday_min31 = (datetime.datetime.now() - datetime.timedelta(31)).strftime('%Y-%m-%d')

    yoy_plot(tddf[:yday].sum(1),f'{workingdir}/images/year_over_year_yesterday.png')

    make_station_map(yday,f'{workingdir}/images/station_map_yesterday.png',workingdir)
    make_station_ani(yday,f'{workingdir}/images/station_ani_yesterday.gif',workingdir)
  
    weather_plot(tddf.sum(1).iloc[-365:],f'{workingdir}/images/lastyear_daily.png',kind='line')
    weather_plot(tddf.sum(1)['2018-01':],f'{workingdir}/images/2018-current_daily.png',kind='line')
    weather_plot(tddf.sum(1).iloc[-30:],f'{workingdir}/images/lastmonth_daily.png',kind='bar',highlight=True)
    weather_plot(tddf.sum(1).loc[yday_min31:yday],f'{workingdir}/images/lastmonth_daily_yesterday.png',kind='bar',highlight=True)

    
    simple_plot(thdf.sum(1).iloc[-7*24:-1],f'{workingdir}/images/lastweek_hourly.png',kind='line')
    simple_plot(thdf.sum(1).loc[yday_min7:yday],f'{workingdir}/images/lastweek_hourly_yesterday.png',kind='line',highlight=True)
    
    cumsum_plot(thdf[thisyear:],f'{workingdir}/images/today_cumsum.png')    
    cumsum_plot(thdf[thisyear:yday],f'{workingdir}/images/yesterday_cumsum.png')


#     p = Plot().draw(tddf.sum(1).iloc[-365:],imdir+'lastyear_daily.png',weather=True)
#     p = Plot().draw(tddf.sum(1).iloc[-30:],imdir+'lastmonth_daily.png',kind='bar',weather=True,highlight=True)    
#     p = Plot().draw(thdf.sum(1).iloc[-7*24:-1],imdir+'lastweek_hourly.png',kind='line')
#     #print("Drawing plots")
#     #Plot().draw(tddf.sum(1),imdir+'alltime_rolling.png',weather=True,rolling=7)
#     p = Plot().draw(thdf.sum(1).loc[yday_min7:yday],imdir+'lastweek_hourly_yesterday.png')
#     p = Plot().draw(thdf[thisyear:],imdir+'today_cumsum.png',kind='cumsum')
#     p = Plot().draw(thdf[thisyear:yday],imdir+'yesterday_cumsum.png',kind='cumsum')
#     p = Plot().draw(tddf.sum(1).loc[yday_min31:yday],
#                 imdir+'lastmonth_daily_yesterday.png',
#                 kind='bar',weather=True,highlight=True)
    

    
    plt.close('all')
    
def update_stations(workingdir):
    dailydf  = get_dailydf(workingdir)
    avail_df = pd.pivot_table(dailydf,columns='name',index='time',values='avl_bikes').iloc[-1]
    op_df    = pd.pivot_table(dailydf,columns='name',index='time',values='operative').iloc[-1]

    avail_df[op_df==False] = -1

    avail_df = pd.DataFrame(avail_df).transpose()
    avail_df.index = [x.strftime('%Y-%m-%d') for x in avail_df.index]

    try:
        stations_df = load_csv(workingdir+'/stations_daily_df.csv')
        stations_df = pd.concat([stations_df,avail_df],sort=True)
    except:
        stations_df = avail_df

        
    stations_df.to_csv(workingdir+'/stations_daily_df.csv')

def get_status(workingdir):
    stations_df = load_csv(workingdir+'/stations_daily_df.csv')
    avail_bikes = stations_df.iloc[-1]
    n_bikes     = int(sum(avail_bikes[avail_bikes>=0]))
    n_stations  = int(len(avail_bikes[avail_bikes>=0]))
    n_closed    = int(sum(avail_bikes[avail_bikes<0]))


    return {'bikes':n_bikes,'stations':n_stations}    
    
def daily_summary(workingdir):
    # Get stats for text
    yesterday = datetime.date.today() - datetime.timedelta(1)
    d = yesterday.strftime('%Y-%m-%d')

    thdf = load_csv(f'{workingdir}/taken_hourly_df.csv')
    rhdf = load_csv(f'{workingdir}/returned_hourly_df.csv')
    ahdf = thdf + rhdf
    tddf = thdf.groupby(pd.Grouper(freq='d')).sum()
    sdf = get_stationsdf(workingdir)

    total_trips = int(tddf.loc[d].sum())



    # Get nth rank in current year
    y = yesterday.strftime('%Y')
    rankdf = tddf[y].sum(1).sort_values(ascending=False).reset_index()
    rank = rankdf[rankdf['time']==yesterday].index[0] + 1


    # Check that we still have data to the beginning of the year. If not tweet for help
    jan01 = y + '-01-01'
    trips_jan01 = int(tddf.loc[jan01].sum())

    if trips_jan01 < 1:
        raise ValueError("We need data going back to January 1st for this to work")


        # This is magic from Stack Overflow
    def ordinal(n):
        if n == 1:
            return ""
        return " {}{}".format(n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])

    rankstring = ordinal(rank)


    # Decide whether a ranking gets an exclamation mark
    if rank < 5:
        punct = '!'
    else:
        punct = '.'


    # Get other stats
    status = get_status(workingdir)

    active_stations = sdf.loc[sdf['active'],'name']

    a24df = ahdf.loc[d,active_stations].sum()
    station24h = a24df.idxmax()
    station24hmin = a24df.idxmin()

    maxstationtrips = int(a24df.max())
    minstationtrips = int(a24df.min())


    nstationsmax = len(a24df[a24df == maxstationtrips])
    nstationsmin = len(a24df[a24df == minstationtrips])



    if nstationsmax > 1:
        max_others_string = "and {} others".format(nstationsmax-1)
    else: 
        max_others_string = ""
    if nstationsmin > 1:
        min_others_string = "and {} others".format(nstationsmin-1)
    else:
        min_others_string = ""




    # Text string
    s ="""Yesterday there were approximately {} mobi trips. That's the{} most this year{}
Active stations: {}
Active bikes: {}
Most used station: {} {} ({} trips)
Least used station: {} {} ({} trips)
#bikeyvr""".format(total_trips,rankstring,punct,
                   status['stations'],status['bikes'],
                   station24h,max_others_string,maxstationtrips,
                   station24hmin,min_others_string,minstationtrips)



    # Upload images
    ims = [f'{workingdir}/images/lastweek_hourly_yesterday.png',
           f'{workingdir}/images/lastmonth_daily_yesterday.png',
           f'{workingdir}/images/year_over_year_yesterday.png',
           f'{workingdir}/images/station_map_yesterday.png'
               ]
        #media_ids = [api.media_upload(x).media_id for x in ims]


    
    return s, ims
