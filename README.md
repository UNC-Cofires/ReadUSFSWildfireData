# ReadUSFSWildfireData
data + mapping on wildfire growth


## Getting Started

### Dependencies

Python Libraries:

* geopandas
* numpy
* pandas
* datashader
* matplotlib
* plotly

### Executing program

* go to US Fire Service data website at https://www.fs.usda.gov/rds/archive/catalog/RDS-2013-0009.6:
* download fire data file FPA_FOD_20221014.gpkg, put in repository
* disaggregate file into state-level shapefiles using
```
python -W ignore spark_disagg.py
```
* create html files mapping wildfire data:
```
python -W ignore spark_analysis.py
```
