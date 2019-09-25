import pandas as pd
import geopandas 



def load_csv(f):
    df = pd.read_csv(f,index_col=0,parse_dates=[0])
    return df

def get_dailydf(d):
    try:
        ddf = pd.read_csv(d,parse_dates=['time'])
    except:
        ddf = pd.read_csv('{}/daily_mobi_dataframe.csv'.format(d),parse_dates=['time'])
    
    ddf = ddf.dropna(subset=['name','time','id'])
    
    # Place unlocated stations at the nexus of the world
    ddf.coordinates = ddf.coordinates.fillna("0,0")
    # sometimes there are letters in the coords field :/ Get rid of them
    ddf.coordinates = ddf.coordinates.replace(regex=True,to_replace=r'[A-Za-z]',value=r'')
    ddf.coordinates = ddf.coordinates.map(lambda x: x.split(','))
    ddf.coordinates = ddf.coordinates.map(lambda x: [float(x[0]),float(x[1])])
    return ddf
    

def get_stationsdf(workingdir):
    sdf = geopandas.read_file(f'{workingdir}/stations_df.geojson')
    return sdf

def get_active_stations(workingdir):
    """ Returns list of active stations """
    sdf = get_stationsdf(workingdir)
    active_stations = list(sdf.loc[sdf['active']==True,'name'])
    return active_stations


def sdf_to_latlong(sdf):
    sdf = sdf.to_crs(epsg=4326)
    sdf['coordinates'] = sdf['geometry'].map(lambda x: (x.y,x.x))
    del sdf['geometry']
    return sdf


def add_station_neighbourhoods(workingdir,sdf):

    gdf = geopandas.read_file(f'{workingdir}/shapes/local_area_boundary.shp')

    def f(point):
        hoods = [hoodname for hoodname,hoodpoly in zip(gdf['NAME'],gdf['geometry']) if hoodpoly.contains(point) ]

        if len(hoods) == 0:
            return "Stanley Park"
        else:
            return hoods[0]


    sdf['neighbourhood'] = sdf['geometry'].map(lambda x: f(x))

    return sdf




def update_stations_df(workingdir):
    ddf = get_dailydf(workingdir)
    ddf = ddf.drop_duplicates('name').copy()
    ddf = ddf[['coordinates','name']]
    ddf['coordinates'] = ddf['coordinates'].map(lambda x:tuple(x))
    ddf = ddf.set_index('name')
    ddf['lat'] = ddf['coordinates'].map(lambda x: x[0])
    ddf['long'] = ddf['coordinates'].map(lambda x: x[1])
    
    ddf = geopandas.GeoDataFrame(ddf,
                                 geometry=geopandas.points_from_xy(ddf['long'],ddf['lat']), 
                                 crs={'init' :'epsg:4326'}
                                )

    ddf = ddf[ddf.lat>0]
    ddf['active'] = True
    ddf = ddf[['geometry','active']].reset_index()
    ddf = ddf.to_crs({'init':'epsg:26910'})
    
    try: # If file already exists
        sdf = geopandas.read_file('stations_df.geojson')
        sdf = pd.concat([sdf,ddf],sort=True)
        sdf['active'] = [True if x in ddf.index else False for x in sdf.index]
        sdf = sdf[~sdf.index.duplicated(keep='last')]
    except ValueError:
        sdf = ddf

    
    sdf.loc[sdf['name']=='Summer Cinema Mobi Bike Valet (brought to you by BEST/Translink)','active'] = False
    sdf.loc[sdf['name']=='Temporary Events Station','active'] = False

    sdf = add_station_neighbourhoods(workingdir,sdf)

    sdf.to_file(f"{workingdir}/stations_df.geojson", driver='GeoJSON')
    return sdf
