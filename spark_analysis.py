import geopandas as gpd
import pandas as pd
import numpy as np
import datashader as ds
import datashader.transfer_functions as tf
from matplotlib.cm import hot
import plotly.express as px
import plotly.graph_objects as go
import os

# set to most interesting fire states
state_list = ['TX', 'AZ', 'MT']
# same range aggregation period as in spark_disagg
year_agg_period = 5
final_year = 2020
# loop through selected states
for st in state_list:
  # what type of fires are we plotting?
  for map_type in ['all_fire', 'large_fire', 'power_equip', 'power_equip_large_fire']:
    agg_dict = {} # dictionary for datashader aggregation
    coord_dict = {} # dictionary to map grid array to coordinate system
    start_year = 1990 # same range aggregation period as in spark_disagg
    # save min/max values so all periods have the same color scale
    max_val_all = 0
    min_val_all = 999999
    # same loop as in spark_disagg
    while start_year < final_year:
      print(st, end = " ")
      print(start_year)
      # read state-level shapefiles
      filepath_name = os.path.join(st, st + '_' + str(start_year + 1) + '-' + str(start_year + year_agg_period) + '.shp')
      state_year_spark_gdf = gpd.read_file(filepath_name)
      # what is the resolution of the datashader aggregation for each fire type
      # if fire type is not 'all_fire', slice data accordingly
      if map_type == 'all_fire':
        agg_type = 'log'
        pixels = 1000
      if map_type == 'large_fire':
        col_nm = 'FIRE_SIZE'
        type_id = 10 # min size in acres 'large fire'
        state_year_spark_gdf = state_year_spark_gdf[state_year_spark_gdf[col_nm] > type_id]
        agg_type = 'linear'
        pixels = 200
      elif map_type == 'power_equip':
        col_nm = 'NWCG_GENER'
        type_id = 'Power generation/transmission/distribution' # fires caused by elec. power infra.
        state_year_spark_gdf = state_year_spark_gdf[state_year_spark_gdf[col_nm] == type_id]
        agg_type = 'linear'
        pixels = 200
      elif map_type == 'power_equip_large_fire':
        col_nm = 'NWCG_GENER'
        col_nm2 = 'FIRE_SIZE'
        type_id = 'Power generation/transmission/distribution' # fires caused by elec. power infra.
        type_id2 = 10 # min size in acres 'large fire'
      
        state_year_spark_gdf = state_year_spark_gdf[np.logical_and(
                             state_year_spark_gdf[col_nm] == type_id,
                             state_year_spark_gdf[col_nm2] > type_id2)]
        agg_type = 'linear'
        pixels = 200
    
      # get coord. bounds of state data
      minx, miny, maxx, maxy = state_year_spark_gdf.total_bounds
      plot_width = maxx - minx
      plot_height = maxy - miny
      
      # give x/y coords as shapefile features
      state_year_spark_df = pd.DataFrame()
      state_year_spark_df['x'] = state_year_spark_gdf.geometry.x
      state_year_spark_df['y'] = state_year_spark_gdf.geometry.y

      # size datashader grid proportionally to height/width
      if plot_height > plot_width:
        plot_width_use = int(pixels * float(plot_width) / float(plot_height))
        plot_height_use = pixels
      else:
        plot_width_use = pixels
        plot_height_use = int(pixels * float(plot_height) / float(plot_width))
 
      # aggregate data with datashader
      cvs = ds.Canvas(plot_width = plot_width_use, plot_height = plot_height_use)
      agg = cvs.points(state_year_spark_df, 'x', 'y', ds.count())
      # get min/max of data for consistent colorscale
      max_val_all = max(max_val_all, int(agg.max()))
      min_val_all = min(min_val_all, int(agg.min()))
      
      # get coordinates of grid aggregation
      coords_lat, coords_lon = agg.coords['y'].values, agg.coords['x'].values
      coordinates = [[coords_lon[0], coords_lat[0]],  
                     [coords_lon[-1], coords_lat[0]],
                     [coords_lon[-1], coords_lat[-1]],
                     [coords_lon[0], coords_lat[-1]]]  
      # save aggregation and grid coordinate system                     
      agg_dict[start_year] = agg
      coord_dict[start_year] = coordinates
      start_year += year_agg_period
    
    # put all aggregations into a list for plotly buttons
    all_imgs = []
    all_imgs_dict = {}
    for start_year in agg_dict:
      # turn data array into image for plotting
      all_imgs.append({"sourcetype": "image",
                     "source": (tf.shade(agg_dict[start_year], cmap = hot, 
                                         how=agg_type, span = [min_val_all, max_val_all]))[::-1].to_pil(),
                     "coordinates": coord_dict[start_year]
                     })
      all_imgs_dict[start_year] = {"sourcetype": "image",
                     "source": (tf.shade(agg_dict[start_year], cmap = hot, 
                                         how=agg_type, span = [min_val_all, max_val_all]))[::-1].to_pil(),
                     "coordinates": coord_dict[start_year]
                     }
    # initialize mapbox with single value (value is not relevant/important)
    fig = px.scatter_mapbox(state_year_spark_df.tail(1), 
                      lat='y', 
                      lon='x', 
                      zoom=5,width=1000, height=1000) 
    
    # layout plotly figure with all images
    fig.update_layout(mapbox_style="carto-darkmatter",
                    mapbox_layers = all_imgs
                     )
    # map buttons to the correct image
    # this displays all images with 'All' button
    buttons_use = []
    start_year = 1990
    buttons_use.append({"label": 'All',
                        "method": "update",
                        "args": [{'visible':[]},
                                 {'title': st + ' All Years',           
                                  'mapbox':{
                                           'style':fig.layout.mapbox.style,
                                           'center': fig.layout.mapbox.center,
                                           'zoom': fig.layout.mapbox.zoom,
                                           'layers': all_imgs
                                          },
                                  },],
                      })
    # map 5-year periods to correct button label
    while start_year < final_year:
      buttons_use.append({"label": str(start_year + 1) + '-' + str(start_year + year_agg_period),
                          "method": "update",
                          "args": [{'visible':[]},
                                   {'title': st + ' ' + str(start_year + 1) + '-' + str(start_year + year_agg_period),           
                                    'mapbox':{
                                             'style':fig.layout.mapbox.style,
                                             'center': fig.layout.mapbox.center,
                                             'zoom': fig.layout.mapbox.zoom,
                                             'layers': [all_imgs_dict[start_year]]
                                             },
                                    },],
                          })
      start_year += year_agg_period
    
    # set figure layout
    fig.update_layout(updatemenus = [{'buttons':buttons_use}])             
    colorbar_trace = go.Scatter(x=[None],
                                y=[None],
                                mode='markers',
                                marker=dict(
                                    colorscale='hot', 
                                    showscale=True,
                                    cmin=min_val_all,
                                    cmax=max_val_all,
                                    colorbar=dict(thickness=25, title = '# of Fires',
                                    tickvals=[min_val_all, min_val_all + (max_val_all - min_val_all)/2, max_val_all], 
                                    ticktext=[min_val_all, agg_type + ' scale', max_val_all], outlinewidth=0)
                                  ),
                                hoverinfo='none'
                                )
    # format fig, add colorbar, write to file
    fig['layout']['showlegend'] = False
    fig.add_trace(colorbar_trace)
    fig.write_html(os.path.join(st, st + '_' + map_type + '.html'))
