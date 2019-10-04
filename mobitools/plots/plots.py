#!/home/msj/miniconda3/bin/python3



import matplotlib as mpl
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties

from jinja2 import Environment, FileSystemLoader
import time
import datetime
import mobitools.weather.vanweather as vw
from mobitools.core.helpers import *
import matplotlib.lines as mlines
import os

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

#print('Setting MPL defaults')
#https://matplotlib.org/users/customizing.html
colors = ['#3778bf','#7bb274','#825f87',
          '#feb308','#59656d','#984447',
          '#e17701','#add9f4','#1b264f',
          '#4b296b','#380835','#607c8e',
          '#ca6641']
# colors = ['#3778bf','#7bb274',,'#feb308',
#               '#59656d']

mpl.rcParams['axes.prop_cycle'] = mpl.cycler('color',colors)
bg_color = '#ffffff'
fg_color = colors[1]
fg_color2 = colors[0]
fg_color3 = colors[3]
fg_color4 = colors[2]
ax_color = colors[4]

mpl.rcParams['font.family'] = 'sans-serif'
#mpl.rcParams['font.sans-serif'] = ['Helvetica']
plt.rc('text', color=ax_color)
#plt.rc('axes',titleweight='bold')

mpl.rcParams['axes.spines.right'] = False
mpl.rcParams['axes.spines.top'] = False
mpl.rcParams['axes.edgecolor'] = ax_color
mpl.rcParams['ytick.color'] = ax_color
mpl.rcParams['xtick.color'] = ax_color
mpl.rcParams['axes.labelcolor'] = ax_color
mpl.rcParams['axes.labelsize'] = 13
mpl.rcParams["figure.figsize"] = (7,5)




def yoy_plot(df,fname):
    
    yday_day = (datetime.datetime.now() - datetime.timedelta(1)).day
    yday_month = (datetime.datetime.now() - datetime.timedelta(1)).month
    
    todaydf = df[(df.index.month==yday_month) & (df.index.day==yday_day)]
    f,ax = plt.subplots()
    ax.plot(df,color=ax_color,alpha=0.5)
    ax.plot(todaydf.index,todaydf.values,color=fg_color)
    s = ax.scatter(todaydf.index,todaydf.values,color=fg_color)
    
    ax.tick_params(axis='x',labelrotation=45)
    
    labelfont = FontProperties(weight='roman',size=12)

    ax.set_ylabel('Trips')
    
    def get_text(date):
        wdf = vw.get_monthly_weather(date.strftime('%Y'),date.strftime('%m'))
        text = f"{date.strftime('%A, %b %d %Y')}\nDaily High: {wdf.loc[date.strftime('%Y-%m-%d'),'Max Temp']}°C\nPrecipitation: {wdf.loc[date.strftime('%Y-%m-%d'),'Total Precipmm']}mm"
        return text
    
    try:
        texts = [get_text(x) for x in todaydf.index]
    except:
        texts = [x for x in todaydf.index]
        
    for c,text in zip(s.get_offsets().data,texts):
        ax.annotate(text,c,color=fg_color,
                textcoords='offset points',xytext=(-60,-50),
                bbox=dict(boxstyle="round",fc='w',ec='w',alpha=0.9),
                fontproperties=labelfont
                #arrowprops=dict(arrowstyle = '-|>',color='k',alpha=0.5)
               )    
        
    f.tight_layout()
    f.savefig(fname)
    
def simple_plot(df,fname,kind='line',highlight=False):
    f,ax = plt.subplots()

    if kind == 'line':
        
        if highlight:
            line = ax.plot(df[:-24].index,df.values[:-24],color=fg_color,alpha=0.3)
            ax.fill_between(df.index[:-24],0,df.values[:-24],color=fg_color,alpha=0.2)
            line = ax.plot(df.index[-25:],df.values[-25:],color=fg_color)
            ax.fill_between(df.index[-25:],0,df.values[-25:],color=fg_color,alpha=0.8)
        else:    
            line = ax.plot(df.index,df.values,color=fg_color)
            ax.fill_between(df.index,0,df.values,color=fg_color,alpha=0.8)

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%A"))
        ax.xaxis.get_ticklabels()[-1].set_visible(False) # removes the rightmost tick label
            
    if kind=='bar':
        bars = ax.bar(df.index,df.values,color=fg_color)
        # set ticks every week
        ax.xaxis.set_major_locator(mdates.WeekdayLocator())
        #set major ticks format
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        if highlight:
            [x.set_alpha(0.6) for x in bars[:-1]]
    ax.tick_params(axis='x',labelrotation=45)
    ax.set_ylabel('Trips')    
    f.tight_layout()
    f.savefig(fname)
    return f,ax

def weather_plot(df,fname,kind='line',highlight=False):
    f,(ax,wax) = plt.subplots(2,sharex=True,gridspec_kw={'height_ratios':[4.5,1]})

    if kind == 'line':
        line = ax.plot(df.index,df.values,color=fg_color)
        ax.fill_between(df.index,0,df.values,color=fg_color,alpha=0.8)

    if kind=='bar':
        bars = ax.bar(df.index,df.values,color=fg_color)
        # set ticks every week
        ax.xaxis.set_major_locator(mdates.WeekdayLocator())
        #set major ticks format
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        if highlight:
            [x.set_alpha(0.6) for x in bars[:-1]]
    ax.set_ylabel('Trips')
            
    wdf = vw.get_weather_range(df.index[0].strftime('%Y-%m'),
                                    (df.index[-1]-datetime.timedelta(1)).strftime('%Y-%m'))
    wdf = wdf.loc[[x for x in wdf.index if x in df.index],:]

    wax.bar(wdf.index,wdf['Total Precipmm'],color=fg_color2)
    wax2 = wax.twinx()
    #wax2 = set_ax_props(wax2)
    wax2.plot(wdf.index,wdf['Max Temp'],color=fg_color3)
    wax2.set_ylabel('High ($^\circ$C)')
    wax2.yaxis.label.set_color(fg_color3)
    wax.set_ylabel('Rain (mm)')
    wax.yaxis.label.set_color(fg_color2)
    wax.spines['right'].set_visible(True)
    wax2.spines['right'].set_visible(True)
    wax.tick_params(axis='x',labelrotation=45)
    wax2.tick_params(axis='x',labelrotation=45)

    f.tight_layout()
    f.savefig(fname)
    
    return f,ax
    
def cumsum_plot(df,fname): 
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    thisyear = datetime.datetime.now().strftime('%Y')
    f,ax = plt.subplots()
    def cumsum(df):

        df = df.sum(1).cumsum()
        df.index = df.index.map(lambda x: x.strftime('%H:%M'))
        df = df.shift()
        df.iloc[0] = 0
        return df

    for i,df in df.groupby(pd.Grouper(freq='d')):
        try:
            df = cumsum(df)
            ax.plot(df.index,df,color='gray',alpha=0.1)
        except IndexError:
            pass
    #print(df.head())
    ax.plot(df.index,df,alpha=1,color=fg_color)
    ax.scatter(df.index,df,alpha=1,color=fg_color)
    ax.set_ylabel("Hourly Cumulative Trips",color=ax_color)
    ax.set_xlabel("Time",color=ax_color)


    #year = df.index[-1].year
    #date = df.index[-1].date().strftime('%Y-%m-%d')
    gray_line = mlines.Line2D([], [], color=ax_color,  label="{} so far".format(thisyear))
    green_line= mlines.Line2D([], [], color=fg_color, marker='.',label="{}".format(today))
    ax.legend(handles=[green_line,gray_line])
    ax.tick_params(axis='x',labelrotation=45)
    f.tight_layout()
    f.savefig(fname)
    return f,ax
    
def make_station_map(date,fname,workingdir):
   
    #Load mobi daily data
    thdf = load_csv(workingdir+'/taken_hourly_df.csv')
    rhdf = load_csv(workingdir+'/returned_hourly_df.csv')
    tddf = thdf.groupby(pd.Grouper(freq='d')).sum()
    rddf = rhdf.groupby(pd.Grouper(freq='d')).sum()
    
    # Load stations geoDF  
    sdf = get_stationsdf(workingdir)
    
    
    # Get day's trip counts
    addf = tddf + rddf
    addf = addf[sdf.loc[sdf['active'],'name']]
    trips = addf.loc[date].reset_index()
    trips.columns = ['name','trips']   
    
    # make sure geoDF is on the left so it stays a geoDF
    sdf = pd.merge(sdf, trips, how='inner',on='name')
    
    bikeways_df = geopandas.read_file(f'{workingdir}/shapes/bikeways.shp')
    shoreline_df = geopandas.read_file(f'{workingdir}/shapes/shoreline2002.shp')
    
    
    f,ax = plt.subplots()
    bikeways_df.plot(ax=ax,color=fg_color)
    shoreline_df.plot(ax=ax,color='k')
    left = 485844
    right = 495513
    bottom = 5453579
    top = 5462500
    ax.axis('off')
    ax.set_xlim(left,right)
    ax.set_ylim(bottom,top)
    
    # Dummy scatters for the legend
    l1 = ax.scatter([0],[0], s=10, edgecolors='none',color=fg_color2,alpha=0.7)
    l2 = ax.scatter([0],[0], s=100, edgecolors='none',color=fg_color2,alpha=0.7)
    l3 = ax.scatter([0],[0], s=10, marker='x',edgecolors='none',color=fg_color4,alpha=0.7)

    labels=['0','10','100']
    ax.legend([l3,l1,l2],labels,title=f'Station Activity\n{date}')
    
    
    sdf.plot(ax=ax,markersize=list(sdf['trips']), alpha=0.7, zorder=100, color=fg_color2)
    
    sdf[sdf.trips==0].plot(ax=ax,color=fg_color4,alpha=0.7,markersize=10,marker='x',zorder=100)
    

    
    f.savefig(fname,bbox_inches='tight',pad_inches=0.0,transparent=False)
    
    
    
if __name__ == '__main__':
    weather_plot(tddf.sum(1).iloc[-365:],'./images/lastyear_daily.png',kind='line')
    weather_plot(tddf.sum(1)['2018-01':],'./images/2018-current_daily.png',kind='line')
    weather_plot(tddf.sum(1).iloc[-30:],'./images/lastmonth_daily.png',kind='bar',highlight=True)
    weather_plot(tddf.sum(1).loc[yday_min31:yday],'./images/lastmonth_daily_yesterday.png',kind='bar',highlight=True)

    
    simple_plot(thdf.sum(1).iloc[-7*24:-1],'./images/lastweek_hourly.png',kind='line')
    simple_plot(thdf.sum(1).loc[yday_min7:yday],'./images/lastweek_hourly_yesterday.png',kind='line')
    
    cumsum_plot(thdf[thisyear:],'./images/today_cumsum.png')    
    cumsum_plot(thdf[thisyear:yday],imdir+'yesterday_cumsum.png')
    
    make_station_map(yday,imdir+'station_map_yesterday.png',workingdir)
    make_station_ani(yday,imdir+'station_ani_yesterday.gif',workingdir)
    
    
       # p = Plot().draw(thdf.sum(1).iloc[-7*24:-1],imdir+'lastweek_hourly.png',kind='line')
    #print("Drawing plots")
    #Plot().draw(tddf.sum(1),imdir+'alltime_rolling.png',weather=True,rolling=7)
    #p = Plot().draw(thdf.sum(1).loc[yday_min7:yday],imdir+'lastweek_hourly_yesterday.png')
    #p = Plot().draw(thdf[thisyear:],imdir+'today_cumsum.png',kind='cumsum')
    #p = Plot().draw(thdf[thisyear:yday],imdir+'yesterday_cumsum.png',kind='cumsum')
    #p = Plot().draw(tddf.sum(1).loc[yday_min31:yday],
    #            imdir+'lastmonth_daily_yesterday.png',
    #            kind='bar',weather=True,highlight=True)
    
    
    
    
