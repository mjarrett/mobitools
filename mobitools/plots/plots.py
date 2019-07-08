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
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import matplotlib.animation as animation
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

# try:
#     thdf = load_csv(f'/home/msj/mobi/taken_hourly_df.csv')
#     thdf.index = pd.to_datetime(thdf.index)
#     tddf = thdf.groupby(pd.Grouper(freq='d')).sum()
# except FileNotFoundError:
#     pass

today = datetime.datetime.now().strftime('%Y-%m-%d')
thisyear = datetime.datetime.now().strftime('%Y')
yday = (datetime.datetime.now() - datetime.timedelta(1)).strftime('%Y-%m-%d')
yday_min7 = (datetime.datetime.now() - datetime.timedelta(8)).strftime('%Y-%m-%d')
yday_min31 = (datetime.datetime.now() - datetime.timedelta(31)).strftime('%Y-%m-%d')
yday_day = (datetime.datetime.now() - datetime.timedelta(1)).day
yday_month = (datetime.datetime.now() - datetime.timedelta(1)).month

def yoy_plot(df,fname):
    
    todaydf = df[(df.index.month==yday_month) & (df.index.day==yday_day)]
    f,ax = plt.subplots()
    ax.plot(df,color=ax_color,alpha=0.5)
    ax.plot(todaydf.index,todaydf.values,color=fg_color)
    s = ax.scatter(todaydf.index,todaydf.values,color=fg_color)
    
    ax.tick_params(axis='x',labelrotation=45)
    
    labelfont = FontProperties(weight='roman',size=13)

    ax.set_ylabel('Trips')
    

    for c,i in zip(s.get_offsets().data,todaydf.index):
        ax.annotate(i.strftime('%Y-%m-%d'),c,color=fg_color,
                textcoords='offset points',xytext=(-60,-30),
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
    

    
def cumsum_plot(df,fname): 
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
    
class GeoPlot():
    def __init__(self,n=1,m=0):

        #super().__init__(n,m)

        self.f, self.ax = plt.subplots()
        self.f.subplots_adjust(left=0, bottom=0.05, right=1, top=1, wspace=None, hspace=None)
        self.ax = plt.axes(projection=ccrs.epsg(26910),frameon=False)

        # This is a workaround... frameon=False should work in future versions of cartopy
        self.ax.outline_patch.set_visible(False)

        self.left = 485844
        self.right = 495513
        self.bottom = 5453579
        self.top = 5462500

        self.ax.set_extent([self.left,self.right,self.bottom,self.top ], ccrs.epsg(26910))
        
#         self.ax.text(self.right,self.bottom-400,'@VanBikeShareBot',
#                      color=fg_color,size=18,
#                      alpha=0.6,horizontalalignment='right')
             
        
    def addgeo(self,shapef,edgecolor='black',facecolor='white',alpha=1,zorder=1):
        shape = list(shpreader.Reader(shapef).geometries())
        record = list(shpreader.Reader(shapef).records())
        self.ax.add_geometries(shape, ccrs.epsg(26910),
                      edgecolor=edgecolor, facecolor=facecolor, alpha=alpha,zorder=zorder)
        return shape, record    
        
    
    def draw(self,sdf,date):
        sdf['lat'] = sdf['coordinates'].map(lambda x: x[0])
        sdf['long'] = sdf['coordinates'].map(lambda x: x[1])

        self.ax.scatter(sdf.long,sdf.lat,transform=ccrs.PlateCarree(),alpha=0.7,
                        s=sdf['trips'],color=fg_color2,zorder=100)
        
        stations_null = self.ax.scatter(sdf.long[sdf.trips==0],
                               sdf.lat[sdf.trips==0],
                               transform=ccrs.PlateCarree(),
                               color=fg_color4,alpha=0.7,s=10,marker='x',
                                        zorder=100)
       
        # Dummy scatters for the legend
        l1 = self.ax.scatter([0],[0], s=10, edgecolors='none',color=fg_color2,alpha=0.7)
        l2 = self.ax.scatter([0],[0], s=100, edgecolors='none',color=fg_color2,alpha=0.7)
        l3 = self.ax.scatter([0],[0], s=10, marker='x',edgecolors='none',color=fg_color4,alpha=0.7)
       
        labels=['0','10','100']
        self.ax.legend([l3,l1,l2],labels,title='Station Activity\n{}'.format(date))

        return self.f
        
        f.savefig(fname,bbox_inches='tight',pad_inches=0.0,transparent = True)

    
def make_station_map(date,fname,workingdir):
    #workingdir='/data/mobi/data/'
   
    #Load mobi daily data
    thdf = load_csv(workingdir+'/taken_hourly_df.csv')
    rhdf = load_csv(workingdir+'/returned_hourly_df.csv')
    tddf = thdf.groupby(pd.Grouper(freq='d')).sum()
    rddf = rhdf.groupby(pd.Grouper(freq='d')).sum()
    addf = tddf + rddf
    ddf = get_dailydf(workingdir)
    

    # Get day's trip counts
    trips = addf.loc[date].reset_index()
    trips.columns = ['name','trips']

    
    sdf = get_stationsdf(workingdir)
    sdf = pd.merge(trips, sdf, how='inner',on='name')
    #print(sdf.loc[0,'coordinates'][0]/2)
    
    
    plot = GeoPlot()
    plot.addgeo('/home/msj/shapes/bikeways.shp',facecolor="none",edgecolor='green',zorder=95)
    plot.addgeo('/home/msj/shapes/shoreline2002.shp',facecolor='#ffffff',zorder=1)
    f = plot.draw(sdf,date)
    

        
    f.savefig(fname,bbox_inches='tight',pad_inches=0.0,transparent=True)
    
    
    
def make_station_ani(date1,fname,workingdir,days=1,spark=True):
    #workingdir='/data/mobi/data'

    date2 = (datetime.datetime.strptime(date1,'%Y-%m-%d') +  datetime.timedelta(days-1)).strftime('%Y-%m-%d')
    

    #Load mobi daily data
    thdf = load_csv(workingdir+'/taken_hourly_df.csv')
    rhdf = load_csv(workingdir+'/returned_hourly_df.csv')
    ahdf = thdf	+ rhdf
    
    sdf = get_stationsdf(workingdir)
    # Only active stations
    ahdf = ahdf[sdf.loc[sdf['active'],'name']]
    
    # Get day's trip counts
    trips = ahdf.loc[date1:date2].iloc[0].reset_index()
    trips.columns = ['name','trips']
    # Add yesterday's trip counts
    df = pd.merge(trips, sdf, how='inner',on='name')
    df['lat'] = df['coordinates'].map(lambda x:x[0])
    df['long'] = df['coordinates'].map(lambda x:x[1])

    #df = pd.merge(trips, ddf, how='inner',on='name')
    plot = GeoPlot()
    plot.addgeo('/home/msj/shapes/bikeways.shp',facecolor="none",alpha=0.5,edgecolor='green',zorder=95)
    plot.addgeo('/home/msj/shapes/shoreline2002.shp',facecolor='#ffffff',zorder=1)

   
    
    plot.f.set_facecolor([0.5,0.5,0.5])
    plot.f.set_size_inches(5,4.7)
    plot.f.subplots_adjust(left=-0.1, right=1.1, bottom=0, top=1)
    
    
    if spark==True:
        # Add small plot of total activity
        ax2 = plot.f.add_axes([0.02, 0.65, 0.2, 0.2])
        ax2.patch.set_alpha(0)
        ax2.set_axis_off()
        scatter2, = ax2.plot(ahdf[date1:date2].sum(1).index[0],
                             ahdf[date1:date2].sum(1).iloc[0],
                             color=fg_color2,marker='o')
        ax2.plot(ahdf[date1:date2].sum(1),color=fg_color2)

    
    ax = plot.f.axes[0]

    # Draw stations
    stations = ax.scatter(df.long,df.lat,
                         color=fg_color2,alpha=0.7,
                         s=10*df['trips'],
                         zorder=100,transform=ccrs.PlateCarree())

                              
                              
                
    # Dummy scatters for the legend
    l1 = ax.scatter([0],[0], s=10, edgecolors='none',color=fg_color2,alpha=0.7)
    l2 = ax.scatter([0],[0], s=100, edgecolors='none',color=fg_color2,alpha=0.7)
    labels=['1','10']
    legend = ax.legend([l1,l2],labels,title="Station Activity",framealpha=0)
    legend.get_title().set_color(fg_color2)
    for lt in legend.get_texts():
        lt.set_color(fg_color2)
    
    def t2s(date):
        #return date.strftime('%Y-%m-%d\n%-I %p')
        return date.strftime('%-I %p')
    
    def d2s(date):
        return date.strftime('%a %b %-d')
    
    #text = ax.text(plot.left+200,plot.top-800,d2s(ahdf.loc[date1:date2].index[0]),size=10,bbox=dict(boxstyle="round",ec=(1., 1.0, 1.0),fc=(1., 1, 1),alpha=0.8))
    text = ax.text(plot.left+200,
                   plot.top-800,
                   t2s(ahdf.loc[date1:date2].index[0]),
                   size=25,color=fg_color2)
    text2 = ax.text(plot.left+250,
                    plot.top-1200,
                    d2s(ahdf.loc[date1:date2].index[0]),
                    size=10,color=fg_color2)
    
    def run(i):
        trips = ahdf.loc[date1:date2].iloc[i].reset_index()
        trips.columns = ['name','trips']
        
        df = pd.merge(trips, sdf, how='inner',on='name')

        stations.set_sizes(df['trips']*10)
        #legend.set_title(ahdf.loc[date1:date2].index[i])
        text.set_text(t2s(ahdf.loc[date1:date2].index[i]))
        text2.set_text(d2s(ahdf.loc[date1:date2].index[i]))
        
        if spark == True:
            scatter2.set_data(ahdf[date1:date2].sum(1).index[i],ahdf[date1:date2].sum(1).iloc[i])
    
    frames=len(ahdf.loc[date1:date2].index)
    ani = animation.FuncAnimation(plot.f, run,frames=frames, interval=1200)
    ani.save(fname,writer='imagemagick')    
    
    
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
    
    
    
    
