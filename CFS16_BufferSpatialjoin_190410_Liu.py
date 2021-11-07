
get_ipython().run_line_magic('matplotlib', 'inline')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point 
from geopandas.tools import sjoin
import pysal as ps
from IPython.display import display

pd.options.display.max_columns = None

cs_dir = '.../spatialfiles_CFS16/'
cs_dir2 = '.../aspatialfiles_CFS16/'


# ### 1. map Provinces, 5 metropolitan areas, and activity locations
prov = gpd.read_file(cs_dir + '2016_Provinces/lpr_000b16a_e.shp')
metropo_all = gpd.read_file(cs_dir + '2016_Census metropolitan areas/lcma000b16a_e.shp')
da = gpd.read_file(cs_dir + '2016_DisseminationAreas/lda_000b16a_e.shp')
metropo5 = metropo_all[(metropo_all.CMANAME == 'Halifax') | (metropo_all.CMANAME == 'Montréal') | (metropo_all.CMANAME == 'Toronto') | (metropo_all.CMANAME == 'Edmonton') |        (metropo_all.CMANAME == 'Vancouver')]
metropo5.CMANAME.replace('Montréal','Montreal', inplace = True) #prepare for linkage later
da5 = da[(da.CMANAME=='Toronto')|(da.CMANAME=='Halifax')|(da.CMANAME=='Montréal')|(da.CMANAME=='Edmonton')|(da.CMANAME=='Vancouver')]

# load activity locations
actloc_16 = pd.read_csv('./outputs_CFS16/locations.csv', header=0, index_col=None)

# create geopandas object
# setting a coordinates reference system (in this case: lon/lat is WGS84)
# reproject to the crs used in CanadaStatisticsBoundries (like prov, also align with metropo5, da5)
actloc_16['Coordinates'] = list(zip(actloc_16.lon, actloc_16.lat))
actloc_16['Coordinates'] = actloc_16['Coordinates'].apply(Point)
actloc_16 = gpd.GeoDataFrame(actloc_16, crs={'init':'epsg:4326'}, geometry='Coordinates').to_crs(prov.crs)

# add the column `S1A_city` in `actloc_17`
ana_link = pd.read_csv(cs_dir2 + '2016CFS_S1A_combineUserLinkAnaDaysDura_20181129_Liu.csv', sep=',', header=0, index_col=None)
ana_link.S1A_city.replace([1,2,3,4,5], ['Toronto','Montreal','Halifax','Edmonton','Vancouver'],inplace = True)
actloc_16 = actloc_16.join(ana_link.set_index('uuid')[['S1A_city']], on = 'user_id', how = 'left')

# save the geopandas object as a shapefile
# cannot save as a shapefile with the boolean column
actloc_16.used.replace([True,False],[1,0],inplace=True)
actloc_16.to_file(cs_dir + 'actloc_16.shp', driver='ESRI Shapefile')
actloc_16 = gpd.read_file(cs_dir + 'actloc_16.shp')
actloc_16.plot(marker='o',markersize=0.05,color='m')

# plot `prov`, `metropo_all`, and `actloc`
f, ax = plt.subplots(nrows = 1, ncols = 1, figsize=(12,9))
plt.axis('equal')
prov.plot(ax = ax, facecolor = 'grey', edgecolor = 'white', alpha = 0.3)
metropo_all.plot(ax=ax, linewidth = 0.1, edgecolor='grey', alpha = 0.3)
metropo5.plot(ax = ax, color = 'pink', linewidth = 0.2, edgecolor = 'r')
da5.plot(ax=ax,facecolor = 'green', edgecolor = 'white', alpha = 0.3)
actloc_16.plot(ax = ax, marker = 'o', markersize = 0.05, color = 'm')
plt.show()

# a number of activity locations fall outides the borders of Canada, and the speicfied 5 metropolitan areas as well.
# make sure that DA matches well with CMA boundaries
f,ax=plt.subplots(1,1)
plt.axis('equal')
metropo5[metropo5.CMANAME =='Toronto'].plot(ax=ax,facecolor = 'grey', edgecolor = 'white', alpha = 0.3)
da5[da5.CMANAME == 'Toronto'].plot(ax=ax,color = 'pink', linewidth = 0.2, edgecolor = 'r')


# ### 2. select the activity locations within the residential metropolitan areas
# two rules: 
# ignore the activity locations outside the borders of census tract metropolitan areas of the residential city; 
# ignore the activity locations outside the boreders of residential metropolitan area yet within the boundaries of other cities (e.g. An Edmontoner visited Toronto)
actloc_sj_Toronto = sjoin(actloc_16, metropo5[metropo5.CMANAME == 'Toronto'], how = 'left', op='within')
actloc_Toronto = actloc_sj_Toronto[actloc_sj_Toronto.S1A_city == actloc_sj_Toronto.CMANAME]
print(actloc_sj_Toronto[actloc_sj_Toronto.CMANAME.isnull() == False].user_id.count()) #2393
print(actloc_sj_Toronto[actloc_sj_Toronto.S1A_city == actloc_sj_Toronto.CMANAME].user_id.count()) #2618
actloc_Toronto
# note that 2393-2168 activity locations in Great Toronto are the points of participants from other cities!

# activity locations in Montreal
actloc_sj_Montreal = sjoin(actloc_16, metropo5[metropo5.CMANAME == 'Montreal'], how = 'left')
actloc_Montreal = actloc_sj_Montreal[actloc_sj_Montreal.S1A_city == actloc_sj_Montreal.CMANAME]
print(actloc_sj_Toronto[actloc_sj_Montreal.CMANAME.isnull() == False].user_id.count() - actloc_sj_Montreal[actloc_sj_Montreal.S1A_city == actloc_sj_Montreal.CMANAME].user_id.count())
# activity locations in Halifax
actloc_sj_Halifax = sjoin(actloc_16, metropo5[metropo5.CMANAME == 'Halifax'], how = 'left')
actloc_Halifax = actloc_sj_Halifax[actloc_sj_Halifax.S1A_city == actloc_sj_Halifax.CMANAME]
print(actloc_sj_Toronto[actloc_sj_Halifax.CMANAME.isnull() == False].user_id.count() - actloc_sj_Halifax[actloc_sj_Halifax.S1A_city == actloc_sj_Halifax.CMANAME].user_id.count())
# activity locations in Vancouver
actloc_sj_Vancouver = sjoin(actloc_16, metropo5[metropo5.CMANAME == 'Vancouver'], how = 'left')
actloc_Vancouver = actloc_sj_Vancouver[actloc_sj_Vancouver.S1A_city == actloc_sj_Vancouver.CMANAME]
print(actloc_sj_Toronto[actloc_sj_Vancouver.CMANAME.isnull() == False].user_id.count() - actloc_sj_Vancouver[actloc_sj_Vancouver.S1A_city == actloc_sj_Vancouver.CMANAME].user_id.count())
# activity locations in Edmonton
actloc_sj_Edmonton = sjoin(actloc_16, metropo5[metropo5.CMANAME == 'Edmonton'], how = 'left')
actloc_Edmonton = actloc_sj_Edmonton[actloc_sj_Edmonton.S1A_city == actloc_sj_Edmonton.CMANAME]
print(actloc_sj_Toronto[actloc_sj_Edmonton.CMANAME.isnull() == False].user_id.count() - actloc_sj_Edmonton[actloc_sj_Edmonton.S1A_city == actloc_sj_Edmonton.CMANAME].user_id.count())

# concat the activity locations in 5 cities
actloc_5cities = pd.concat([actloc_Toronto,actloc_Montreal,actloc_Halifax,actloc_Vancouver, actloc_Edmonton], axis = 0).drop(axis=1,columns='index_right')
actloc_5cities.to_file(cs_dir + '/actloc_5cities.shp', driver='ESRI Shapefile')
actloc_5cities = gpd.read_file(cs_dir + '/actloc_5cities.shp')
actloc_5cities.plot(color = 'm', marker = 'o', markersize = 0.02)

f,ax=plt.subplots(1,1,figsize=(9,6))
prov.plot(ax = ax, facecolor = 'grey', edgecolor = 'white', alpha = 0.3)
metropo5.plot(ax = ax, color = 'pink', linewidth = 0.2, edgecolor = 'r')
actloc_5cities.plot(ax=ax, color = 'm', marker = 'o', markersize = 0.02)
plt.axis('equal')
plt.show()


# ### 3. derive the measures of density <br> 
# ### 3.1. attach the dissemination area (DA) id (`DAUID`) to each activity location in `actloc_5cities`
#'DAUID' is the column name of DA id
actloc_5cities = sjoin(actloc_5cities, da5.loc[:,['DAUID','geometry']], how='left').drop(axis=1,columns='index_right')
actloc_5cities.DAUID = actloc_5cities.DAUID.apply(int)
actloc_5cities.to_file(cs_dir + 'actloc_5cities.shp', driver='ESRI Shapefile')
actloc_5cities = gpd.read_file(cs_dir + 'actloc_5cities.shp')
actloc_5cities.plot(color = 'm', marker = 'o', markersize = 0.02)


# ### 3.2. derive the measure of population density at DA level

# check encoding of the population density csv file
with open(cs_dir2 + '2016_PopDenDA.csv') as f:
    print(f)
popden = pd.read_csv(cs_dir2 + '2016_PopDenDA.csv',sep=',', header=0, index_col=None, encoding='cp1252').rename(columns={'COL0':'DAUID','COL1':'Province code','COL2':'Province name','COL3':'CD code','COL4':'CD name',                             'COL5':'DA name','COL6':'Population2016','COL7':'PopDenKm2','COL8': 'LandAreaKm2'})

actloc_5cities = actloc_5cities.merge(popden.loc[:,['DAUID','PopDenKm2']], how='left',on = 'DAUID')
actloc_5cities.columns.values[-1]='DA_Popden'
actloc_5cities.to_file(cs_dir + 'actloc_5cities.shp', driver='ESRI Shapefile')


# ### 3.3. merge DA_Storecounts with `actloc_5cities`, calculate DA-level MRFEI and DA-level ratio of fast food stores
# output: "actloc_5cities.shp"
actloc_5cities = gpd.read_file(cs_dir + 'actloc_5cities.shp')

sc = gpd.read_file(cs_dir + '2018Toronto_StoreCountDA/DA_StoreCounts.shp')
sc.DAUID = sc.DAUID.apply(int)
actloc_5cities = actloc_5cities.merge(sc.loc[:,['DAUID','1km_NUMSup', '1km_NUMFas', '1km_NUMCon', '1km_NUMGre']], how='left', on='DAUID')
actloc_5cities.rename(columns={'1km_NUMSup':'DA1kmSup', '1km_NUMFas':'DA1kmFas', '1km_NUMCon':'DA1kmCon', '1km_NUMGre':'DA1kmGre'}, inplace=True)
actloc_5cities['DA_MRFEI']= (actloc_5cities['DA1kmFas']+actloc_5cities['DA1kmCon'])/(actloc_5cities['DA1kmSup']+actloc_5cities['DA1kmFas']+actloc_5cities['DA1kmCon']+actloc_5cities['DA1kmGre'])
actloc_5cities['DA_fasRatio']= actloc_5cities['DA1kmFas']/(actloc_5cities['DA1kmSup']+actloc_5cities['DA1kmFas']+actloc_5cities['DA1kmCon']+actloc_5cities['DA1kmGre'])
actloc_5cities.to_file(cs_dir + 'actloc_5cities.shp', driver='ESRI Shapefile')


# ### 3.4. link the DA-level measures intersection density, dwelling density, number of POI, number of transit stops, ALE index, ALE_transit index from 2016 Can ALE dataset to activity locations <br>
# output: "actloc_5cities.shp"
CanALE = pd.read_csv(cs_dir2 + 'CanALE_2016.csv', sep = ',', header = 0, index_col = None)
actloc_5cities = gpd.read_file(cs_dir + 'actloc_5cities.shp')
actloc_5cities = actloc_5cities.join(CanALE.set_index('dauid'),on='DAUID', how='left')
actloc_5cities.loc[:,['int_d','dwl_d','poi','z_int_d','z_dwl_d','z_poi','ale_index','ale_class','transit','z_transit','ale_tranist','ale_transit_class']] = \ 
actloc_5cities.loc[:,['int_d','dwl_d','poi','z_int_d','z_dwl_d','z_poi','ale_index','ale_class','transit','z_transit','ale_tranist','ale_transit_class']].convert_objects(convert_numeric=True)
actloc_5cities.to_file(cs_dir + 'actloc_5cities.shp', driver = 'ESRI Shapefile')
actloc_5cities = gpd.read_file(cs_dir + 'actloc_5cities.shp')


# ### 3.5. calculate the time-weighted DA-level population density, MRFEI, ratio of fast food stores, ale_index, ale_tranis by `pivot_table` <br>
# output: "2016CFS_S1A_twPopdenRelaAle_20181129_Liu.csv" 

# merge `pct_actdura` with `actloc_5cities`
loca2 = pd.read_csv(cs_dir2 + 'CFS16_locapct.csv', index_col= None, header = 0)
actloc_pct = pd.merge(actloc_5cities, loca2[['user_id','location_id','sum_actdura','pct_actdura']],  how='left', \
                      left_on=['user_id','location_i'], right_on = ['user_id','location_id'])
actloc_pct.to_file(cs_dir + 'actloc_pct.shp', driver = 'ESRI Shapefile')
actloc_pct = gpd.read_file(cs_dir + 'actloc_pct.shp')

# calculate the time-weighted population density, MRFEI, and ratio of fast food stores by `pivot_table`
actloc_pct['dur*Popden']=actloc_pct.pct_actdur*actloc_pct.DA_Popden
actloc_pct['dur*MRFEI']=actloc_pct.pct_actdur*actloc_pct.DA_MRFEI
actloc_pct['dur*fasrati']=actloc_pct.pct_actdur*actloc_pct.DA_fasRati
actloc_pct['dur*ale']=actloc_pct.pct_actdur*actloc_pct.ale_index
actloc_pct['dur*aletran'] = actloc_pct.pct_actdur*actloc_pct.ale_tranis

pt = actloc_pct.pivot_table(values=['dur*Popden','dur*MRFEI','dur*fasrati','dur*ale','dur*aletran'], \
                            index='user_id', columns=None, aggfunc='sum')
pt.columns = ['DAtwMRFEI','DAtwPopden','DAtwALE','DAtwALEtransit','DAtwFaspct']
pt.to_csv(cs_dir2 + 'CFS16_twDenFas.csv',sep=',',header=True,index=True)
pd.read_csv(cs_dir2 + 'CFS16_twDenFas.csv',sep=',',header=0,index_col=None).head()


# ### 5. buffer (with a radius of 500m, 1000m, 1500m) the activity locations
# directly assign the buffer as the geometry column, which replaces the original point geometry, to maintain the attributes of actloc GeoDataFrame 
actloc_pct = gpd.read_file(cs_dir + 'actloc_pct.shp')
buf_500m = actloc_pct
buf_500m['geometry'] = buf_500m.geometry.buffer(distance = 500)
actloc_pct = gpd.read_file(cs_dir + 'actloc_pct.shp')

buf_1000m = actloc_pct
buf_1000m['geometry'] = buf_1000m.geometry.buffer(distance = 1000)
actloc_pct = gpd.read_file(cs_dir + 'actloc_pct.shp')

buf_1500m = actloc_pct
buf_1500m['geometry'] = buf_1500m.geometry.buffer(distance = 1500)
actloc_pct = gpd.read_file(cs_dir + 'actloc_pct.shp')

f,ax = plt.subplots(1,1, figsize = (9,9))
#metropo5[metropo5.CMANAME == 'Toronto'].plot(ax = ax, facecolor = 'grey', edgecolor = 'black', alpha = 0.3)
buf_500m[buf_500m.S1A_city == 'Toronto'].plot(ax = ax, facecolor = 'pink', edgecolor = 'r', linewidth = 0.1)
actloc_pct[actloc_pct.S1A_city == 'Toronto'].plot(ax=ax, color = 'm', marker = 'o', markersize = 0.03)
plt.axis('equal')
plt.show()

f,ax = plt.subplots(1,1, figsize = (9,9))
#metropo5[metropo5.CMANAME == 'Toronto'].plot(ax = ax, facecolor = 'grey', edgecolor = 'black', alpha = 0.3)
buf_1000m[buf_1000m.S1A_city == 'Toronto'].plot(ax = ax, facecolor = 'pink', edgecolor = 'r', linewidth = 0.1)
actloc_pct[actloc_pct.S1A_city == 'Toronto'].plot(ax=ax, color = 'm', marker = 'o', markersize = 0.03)
plt.axis('equal')
plt.show()

f,ax = plt.subplots(1,1, figsize = (9,9))
#metropo5[metropo5.CMANAME == 'Toronto'].plot(ax = ax, facecolor = 'grey', edgecolor = 'black', alpha = 0.3)
buf_1500m[buf_1500m.S1A_city == 'Toronto'].plot(ax = ax, facecolor = 'pink', edgecolor = 'r', linewidth = 0.1)
actloc_pct[actloc_pct.S1A_city == 'Toronto'].plot(ax=ax, color = 'm', marker = 'o', markersize = 0.03)
plt.axis('equal')
plt.show()


# ### 4. load fast food restaurants
sup = gpd.read_file(cs_dir + '2018_MRFEI_points/supermarket3.shp').to_crs(prov.crs)
con = gpd.read_file(cs_dir + '2018_MRFEI_points/convenience2.shp').to_crs(prov.crs)
fas = gpd.read_file(cs_dir + '2018_MRFEI_points/fast_food2.shp').to_crs(prov.crs)
gre = gpd.read_file(cs_dir + '2018_MRFEI_points/greengrocer2.shp').to_crs(prov.crs)

metropo5.crs = prov.crs

f, ax = plt.subplots(nrows = 1, ncols = 1, figsize=(12,9))
plt.axis('equal')
prov.plot(ax = ax, facecolor = 'grey', edgecolor = 'white', alpha = 0.3)
#metropo_all.plot(ax=ax, linewidth = 0.1, edgecolor='grey', alpha = 0.3)
metropo5.plot(ax = ax, color = 'pink', linewidth = 0.2, edgecolor = 'r', alpha =0.8)
sup.plot(ax=ax, color='blue', marker = 'o', markersize = 0.1)
con.plot(ax=ax, color='orange', marker = 'o', markersize = 0.1)
fas.plot(ax=ax, color='red', marker = 'o', markersize = 0.1)
gre.plot(ax=ax, color='green', marker = 'o', markersize = 0.1)
plt.show()

sup5 = sjoin(sup, metropo5.loc[:,['CMANAME','geometry']], how='left').drop(axis=1,columns='index_right')
con5 = sjoin(con, metropo5.loc[:,['CMANAME','geometry']], how='left').drop(axis=1,columns='index_right')
fas5 = sjoin(fas, metropo5.loc[:,['CMANAME','geometry']], how='left').drop(axis=1,columns='index_right')
gre5 = sjoin(gre, metropo5.loc[:,['CMANAME','geometry']], how='left').drop(axis=1,columns='index_right')
sup5 = sup5[(sup5.CMANAME == 'Halifax') | (sup5.CMANAME == 'Montreal') | (sup5.CMANAME == 'Toronto') | (sup5.CMANAME == 'Edmonton') | (sup5.CMANAME == 'Vancouver')]
con5 = con5[(con5.CMANAME == 'Halifax') | (con5.CMANAME == 'Montreal') | (con5.CMANAME == 'Toronto') | (con5.CMANAME == 'Edmonton') | (con5.CMANAME == 'Vancouver')]
fas5 = fas5[(fas5.CMANAME == 'Halifax') | (fas5.CMANAME == 'Montreal') | (fas5.CMANAME == 'Toronto') | (fas5.CMANAME == 'Edmonton') | (fas5.CMANAME == 'Vancouver')]
gre5 = gre5[(gre5.CMANAME == 'Halifax') | (gre5.CMANAME == 'Montreal') | (gre5.CMANAME == 'Toronto') | (gre5.CMANAME == 'Edmonton') | (gre5.CMANAME == 'Vancouver')]

# map the activity locations, activity spaces (buffer areas), and fast food restaurants in each of the 5 cities
f, ax = plt.subplots(nrows = 1, ncols = 1, figsize=(12,9))
plt.axis('equal')
prov.plot(ax = ax, facecolor = 'grey', edgecolor = 'white', alpha = 0.3)
#metropo_all.plot(ax=ax, linewidth = 0.1, edgecolor='grey', alpha = 0.3)
metropo5.plot(ax = ax, color = 'pink', linewidth = 0.2, edgecolor = 'r', alpha =0.8)
sup5.plot(ax=ax, color='blue', marker = 'o', markersize = 0.1)
con5.plot(ax=ax, color='orange', marker = 'o', markersize = 0.1)
fas5.plot(ax=ax, color='red', marker = 'o', markersize = 0.1)
gre5.plot(ax=ax, color='green', marker = 'o', markersize = 0.1)
plt.show()


# ### 5. assign the buf_500m attributes to fast food restaurants intersecting with it using spatialjoin
buf_500m.crs = prov.crs
buf_1000m.crs = prov.crs
buf_1500m.crs = prov.crs

sup_500 = sjoin(sup5,buf_500m, how = 'left')
con_500 = sjoin(con5,buf_500m, how = 'left')
fas_500 = sjoin(fas5,buf_500m, how = 'left')
gre_500 = sjoin(gre5,buf_500m, how = 'left')
sup_1000 = sjoin(sup5,buf_1000m, how = 'left')
con_1000 = sjoin(con5,buf_1000m, how = 'left')
fas_1000 = sjoin(fas5,buf_1000m, how = 'left')
gre_1000 = sjoin(gre5,buf_1000m, how = 'left')
sup_1500 = sjoin(sup5,buf_1500m, how = 'left')
con_1500 = sjoin(con5,buf_1500m, how = 'left')
fas_1500 = sjoin(fas5,buf_1500m, how = 'left')
gre_1500 = sjoin(gre5,buf_1500m, how = 'left')

f, (ax1,ax2,ax3) = plt.subplots(ncols = 3,figsize = (12.8,4.5)) #gridspec_kw={'width_ratios':[1,1,1]}
metropo5[metropo5.CMANAME == 'Toronto'].plot(ax=ax1, facecolor = 'grey', edgecolor = 'black', alpha = 0.1)
buf_500m[buf_500m.S1A_city == 'Toronto'].plot(ax=ax1, facecolor = 'pink', edgecolor = 'red', linewidth = 0.1, alpha = 0.6)
#sup_500[sup_500.S1A_city == 'Toronto'].plot(ax=ax1, color = 'orange' , marker = '.', markersize = 0.02)
#con_500[con_500.S1A_city == 'Toronto'].plot(ax=ax1, color = 'orange' , marker = '.', markersize = 0.02)
fas_500[fas_500.S1A_city == 'Toronto'].plot(ax=ax1, color = 'orange' , marker = '.', markersize = 0.02)
#gre_500[gre_500.S1A_city == 'Toronto'].plot(ax=ax1, color = 'orange' , marker = '.', markersize = 0.02)

metropo5[metropo5.CMANAME == 'Toronto'].plot(ax=ax2, facecolor = 'grey', edgecolor = 'black', alpha = 0.1)
buf_1000m[buf_1000m.S1A_city == 'Toronto'].plot(ax=ax2, facecolor = 'pink', edgecolor = 'red', linewidth = 0.1, alpha = 0.6)
#sup_1000[sup_1000.S1A_city == 'Toronto'].plot(ax=ax2, color = 'orange' , marker = '.', markersize = 0.02)
#con_1000[con_1000.S1A_city == 'Toronto'].plot(ax=ax2, color = 'orange' , marker = '.', markersize = 0.02)
fas_1000[fas_1000.S1A_city == 'Toronto'].plot(ax=ax2, color = 'orange' , marker = '.', markersize = 0.02)
#gre_1000[gre_1000.S1A_city == 'Toronto'].plot(ax=ax2, color = 'orange' , marker = '.', markersize = 0.02)

metropo5[metropo5.CMANAME == 'Toronto'].plot(ax=ax3, facecolor = 'grey', edgecolor = 'black', alpha = 0.1)
buf_1500m[buf_1500m.S1A_city == 'Toronto'].plot(ax=ax3, facecolor = 'pink', edgecolor = 'red', linewidth = 0.1, alpha = 0.6)
#sup_1500[sup_1500.S1A_city == 'Toronto'].plot(ax=ax3, color = 'orange' , marker = '.', markersize = 0.02)
#con_1500[con_1500.S1A_city == 'Toronto'].plot(ax=ax3, color = 'orange' , marker = '.', markersize = 0.02)
fas_1500[fas_1500.S1A_city == 'Toronto'].plot(ax=ax3, color = 'orange' , marker = '.', markersize = 0.02)
#gre_1500[gre_1500.S1A_city == 'Toronto'].plot(ax=ax3, color = 'orange' , marker = '.', markersize = 0.02)

plt.axis('equal')
plt.show()


# ### 6. aggregate supermarket, convenience, fast food, green grocery by each participant
# ### calculate Ratio of fast food stores
# calculate time-weighted ratio of fast food stores
numsup500_act = sup_500.groupby(by=['user_id','location_i']).aggregate({'user_id':'count'})
numsup500_act.columns = ['numsup500_act']
numcon500_act = con_500.groupby(by=['user_id','location_i']).aggregate({'user_id':'count'})
numcon500_act.columns = ['numcon500_act']
numfas500_act = fas_500.groupby(by=['user_id','location_i']).aggregate({'user_id':'count'})
numfas500_act.columns = ['numfas500_act']
numgre500_act = gre_500.groupby(by=['user_id','location_i']).aggregate({'user_id':'count'})
numgre500_act.columns = ['numgre500_act']
numfas500_act

numsup1000_act = sup_1000.groupby(by=['user_id','location_i']).aggregate({'user_id':'count'})
numsup1000_act.columns = ['numsup1000_act']
numcon1000_act = con_1000.groupby(by=['user_id','location_i']).aggregate({'user_id':'count'})
numcon1000_act.columns = ['numcon1000_act']
numfas1000_act = fas_1000.groupby(by=['user_id','location_i']).aggregate({'user_id':'count'})
numfas1000_act.columns = ['numfas1000_act']
numgre1000_act = gre_1000.groupby(by=['user_id','location_i']).aggregate({'user_id':'count'})
numgre1000_act.columns = ['numgre1000_act']

numsup1500_act = sup_1500.groupby(by=['user_id','location_i']).aggregate({'user_id':'count'})
numsup1500_act.columns = ['numsup1500_act']
numcon1500_act = con_1500.groupby(by=['user_id','location_i']).aggregate({'user_id':'count'})
numcon1500_act.columns = ['numcon1500_act']
numfas1500_act = fas_1500.groupby(by=['user_id','location_i']).aggregate({'user_id':'count'})
numfas1500_act.columns = ['numfas1500_act']
numgre1500_act = gre_1500.groupby(by=['user_id','location_i']).aggregate({'user_id':'count'})
numgre1500_act.columns = ['numgre1500_act']

num500join = numsup500_act.join([numcon500_act,numfas500_act,numgre500_act], how='outer')
num500join.fillna(0, inplace=True)
num500join['fasRatio'] = num500join['numfas500_act']/(num500join['numsup500_act']+num500join['numcon500_act']+ \
                                                      num500join['numfas500_act']+num500join['numgre500_act'])
num500join = num500join.join(buf_500m[['user_id','location_i','pct_actdur']].set_index(['user_id','location_i']), how='left')
num500join['twfasRa500'] = num500join['fasRatio'] * num500join['pct_actdur']
twfasRa500 = num500join.groupby(by='user_id', axis=0).aggregate({'twfasRa500':'sum'})

num1000join = numsup1000_act.join([numcon1000_act,numfas1000_act,numgre1000_act], how='outer')
num1000join.fillna(0, inplace=True)
num1000join['fasRatio'] = num1000join['numfas1000_act']/(num1000join['numsup1000_act']+num1000join['numcon1000_act']+ \
                                                         num1000join['numfas1000_act']+num1000join['numgre1000_act'])
num1000join = num1000join.join(buf_1000m[['user_id','location_i','pct_actdur']].set_index(['user_id','location_i']), how='left')
num1000join['twfasRa1000'] = num1000join['fasRatio'] * num1000join['pct_actdur']
twfasRa1000 = num1000join.groupby(by='user_id', axis=0).aggregate({'twfasRa1000':'sum'})

num1500join = numsup1500_act.join([numcon1500_act,numfas1500_act,numgre1500_act], how='outer')
num1500join.fillna(0, inplace=True)
num1500join['fasRatio'] = num1500join['numfas1500_act']/(num1500join['numsup1500_act']+num1500join['numcon1500_act']+ \
                                                         num1500join['numfas1500_act']+num1500join['numgre1500_act'])
num1500join = num1500join.join(buf_1500m[['user_id','location_i','pct_actdur']].set_index(['user_id','location_i']), how='left')
num1500join['twfasRa1500'] = num1500join['fasRatio'] * num1500join['pct_actdur']
twfasRa1500 = num1500join.groupby(by='user_id', axis=0).aggregate({'twfasRa1500':'sum'})

twfasRatio = twfasRa500.join([twfasRa1000, twfasRa1500], how='left')

# calculate number and time-weighted number of fast food stores
numsup500 = sup_500.groupby(by='user_id', axis=0).aggregate({'user_id':'count'})
numsup500.columns = ['numsup500']
numcon500 = con_500.groupby(by='user_id', axis=0).aggregate({'user_id':'count'})
numcon500.columns = ['numcon500']
numfas500 = fas_500.groupby(by='user_id', axis=0).aggregate({'user_id':'count'})
numfas500.columns = ['numfas500']
numgre500 = gre_500.groupby(by='user_id', axis=0).aggregate({'user_id':'count'})
numgre500.columns = ['numgre500']

numsup1000 = sup_1000.groupby(by='user_id', axis=0).aggregate({'user_id':'count'})
numsup1000.columns = ['numsup1000']
numcon1000 = con_1000.groupby(by='user_id', axis=0).aggregate({'user_id':'count'})
numcon1000.columns = ['numcon1000']
numfas1000 = fas_1000.groupby(by='user_id', axis=0).aggregate({'user_id':'count'})
numfas1000.columns = ['numfas1000']
numgre1000 = gre_1000.groupby(by='user_id', axis=0).aggregate({'user_id':'count'})
numgre1000.columns = ['numgre1000']

numsup1500 = sup_1500.groupby(by='user_id', axis=0).aggregate({'user_id':'count'})
numsup1500.columns = ['numsup1500']
numcon1500 = con_1500.groupby(by='user_id', axis=0).aggregate({'user_id':'count'})
numcon1500.columns = ['numcon1500']
numfas1500 = fas_1500.groupby(by='user_id', axis=0).aggregate({'user_id':'count'})
numfas1500.columns = ['numfas1500']
numgre1500 = gre_1500.groupby(by='user_id', axis=0).aggregate({'user_id':'count'})
numgre1500.columns = ['numgre1500']

twnumsup500 = sup_500.groupby(by='user_id', axis=0).aggregate({'pct_actdur':'sum'})
twnumsup500.columns = ['twnumsup500']
twnumcon500 = con_500.groupby(by='user_id', axis=0).aggregate({'pct_actdur':'sum'})
twnumcon500.columns = ['twnumcon500']
twnumfas500 = fas_500.groupby(by='user_id', axis=0).aggregate({'pct_actdur':'sum'})
twnumfas500.columns = ['twnumfas500']
twnumgre500 = gre_500.groupby(by='user_id', axis=0).aggregate({'pct_actdur':'sum'})
twnumgre500.columns = ['twnumgre500']

twnumsup1000 = sup_1000.groupby(by='user_id', axis=0).aggregate({'pct_actdur':'sum'})
twnumsup1000.columns = ['twnumsup1000']
twnumcon1000 = con_1000.groupby(by='user_id', axis=0).aggregate({'pct_actdur':'sum'})
twnumcon1000.columns = ['twnumcon1000']
twnumfas1000 = fas_1000.groupby(by='user_id', axis=0).aggregate({'pct_actdur':'sum'})
twnumfas1000.columns = ['twnumfas1000']
twnumgre1000 = gre_1000.groupby(by='user_id', axis=0).aggregate({'pct_actdur':'sum'})
twnumgre1000.columns = ['twnumgre1000']

twnumsup1500 = sup_1500.groupby(by='user_id', axis=0).aggregate({'pct_actdur':'sum'})
twnumsup1500.columns = ['twnumsup1500']
twnumcon1500 = con_1500.groupby(by='user_id', axis=0).aggregate({'pct_actdur':'sum'})
twnumcon1500.columns = ['twnumcon1500']
twnumfas1500 = fas_1500.groupby(by='user_id', axis=0).aggregate({'pct_actdur':'sum'})
twnumfas1500.columns = ['twnumfas1500']
twnumgre1500 = gre_1500.groupby(by='user_id', axis=0).aggregate({'pct_actdur':'sum'})
twnumgre1500.columns = ['twnumgre1500']

num = numsup500.join([numcon500,numfas500,numgre500, \
                      numsup1000,numcon1000,numfas1000,numgre1000, \
                      numsup1500,numcon1500,numfas1500,numgre1500], how = 'outer')
num.fillna(0, inplace=True)
twnum = twnumsup500.join([twnumcon500,twnumfas500,twnumgre500, \
                          twnumsup1000,twnumcon1000,twnumfas1000,twnumgre1000, \
                          twnumsup1500,twnumcon1500,twnumfas1500,twnumgre1500], how = 'outer')
twnum.fillna(0, inplace=True)
numtwnum = num.join(twnum, how='outer')

# Save the results to "CFS16_FasNum.csv"
FasNum = twfasRatio.join(numtwnum, how='outer').reset_index()
FasNum.rename(columns = {'index': 'user_id'}, inplace=True)
FasNum.fillna(0, inplace=True)
FasNum.to_csv(cs_dir2 + 'CFS16_FasNum_points.csv', sep = ',', header = True, index = False)

# This Python file is a portion of the computational analyses of the following publication.  
# Liu, B., Widener, M., Burgoine, T., & Hammond, D. (2020). Association between time-weighted activity space-based exposures to fast food outlets and fast food consumption among young adults in urban Canada. International Journal of Behavioral Nutrition and Physical Activity, 17, 1-13.
