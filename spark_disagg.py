import geopandas as gpd
import numpy as np
import pandas as pd
import os

state_list = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", 
              "DC", "DE", "FL", "GA", "HI", "ID", "IL", 
              "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
              "MA", "MI", "MN", "MS", "MO", "MT", "NE", 
              "NV", "NH", "NJ", "NM", "NY", "NC", "ND", 
              "OH", "OK", "OR", "PA", "RI", "SC", "SD", 
              "TN", "TX", "UT", "VT", "VA", "WA", "WV", 
              "WI", "WY"]

# database of wildfires 1992 - 2020
spark_file = 'FPA_FOD_20221014.gpkg'
spark_gdf = gpd.read_file(spark_file)
spark_df = pd.DataFrame(spark_gdf)
# write to csv
spark_df.to_csv('fire_data_as_csv.csv')
# disaggregate dataset by state
# group into five year periods
# create shapefiles
year_agg_period = 5
final_year = 2020
for st in state_list:
  # each state gets its own directory
  os.makedirs(st, exist_ok=True)
  # five year periods, first period only has 4 years
  start_year = 1990
  # loop through 5 year periods
  while start_year < final_year:
    print(st, end = " ")
    print(start_year)  
    # slice dataframe by state and year period    
    state_year_spark_gdf = spark_gdf[np.logical_and(
                                        np.logical_and(
                                          spark_gdf['FIRE_YEAR'] > start_year, 
                                          spark_gdf['FIRE_YEAR'] <= start_year + year_agg_period), 
                                        spark_gdf['STATE'] == st)]
    file_write_path = os.path.join(st, st + '_' + str(start_year + 1) + '-' + str(start_year + year_agg_period) + '.shp')
    state_year_spark_gdf.to_file(file_write_path)
    start_year += year_agg_period
    
    
