import pandas as pd

import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import shapely
import pyproj




def load_csv(f):
    df = pd.read_csv(f,index_col=0,parse_dates=[0])
    return df

def get_dailydf(d):
    ddf = pd.read_csv('{}/daily_mobi_dataframe.csv'.format(d),parse_dates=['time'])
    ddf['coordinates'] = ddf['coordinates'].map(lambda x: x.split(','))
    ddf['coordinates'] = ddf['coordinates'].map(lambda x: [float(x[0]),float(x[1])])
    return ddf
    
# ddf = get_dailydf('/data/mobi/data/')
# print(ddf['coordinates'])

def get_stationsdf(workingdir):

    sdf = pd.read_json("{}/stations_df.json".format(workingdir))
    sdf['coordinates'] = sdf['coordinates'].map(lambda x: tuple(x))
    return sdf

def get_active_stations(workingdir):
    """ Returns list of active stations """
    sdf = get_stationsdf(workingdir)
    active_stations = list(sdf.loc[sdf['active']==True,'name'])
    return active_stations

def update_stations_df(workingdir):
    ddf = get_dailydf(workingdir)
    try:
        sdf = pd.read_json('{}/stations_df.json'.format(workingdir))
        sdf = sdf.set_index('name')
    except ValueError:
        sdf = pd.DataFrame(columns=['name','coordinates','active'])
        sdf = sdf.set_index('name')

    ddf = ddf.drop_duplicates('name').copy()
    ddf = ddf[['coordinates','name']]
    ddf['coordinates'] = ddf['coordinates'].map(lambda x:tuple(x))
    ddf = ddf.set_index('name')

    sdf['coordinates'] = sdf['coordinates'].map(lambda x:tuple(x))
    sdf = pd.concat([sdf,ddf],sort=True)
    sdf['active'] = [True if x in ddf.index else False for x in sdf.index]
    sdf = sdf[~sdf.index.duplicated(keep='last')]
    sdf = sdf.reset_index()
    
    sdf = add_station_coords_sdf(sdf)
    
    sdf.to_json('{}/stations_df.json'.format(workingdir))
    return sdf

def add_station_coords_sdf(sdf):
    epsg  = pyproj.Proj(init='epsg:26910')
    pc = pyproj.Proj(proj='latlon')

    shapef = '/home/msj/shapes/local_area_boundary.shp'
    shapes = list(shpreader.Reader(shapef).geometries())
    records = list(shpreader.Reader(shapef).records())


    sdf['coordinates epsg'] = sdf['coordinates'].map(lambda x: pyproj.transform(pc,epsg, x[1],x[0]) )

    def f(coord):
        hoods =  [r.attributes['NAME'] for s,r in zip(shapes,records) if s.contains(shapely.geometry.Point(*coord))]
        if len(hoods) == 0:
            return "Stanley Park"
        else:
            return hoods[0]


    sdf['neighbourhood'] = sdf['coordinates epsg'].map(lambda x: f(x))
    del sdf['coordinates epsg']

    return sdf
