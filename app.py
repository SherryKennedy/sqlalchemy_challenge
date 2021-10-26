# imports including Flask
import numpy as np
import pandas as pd
import datetime as dt
# Python SQL toolkit and Object Relational Mapper (ORM)
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect
from flask import Flask, jsonify

# ctrl-c to stop the server, save code, rerun python app.py, copy paste url
# with /route name

#################################################
# Database Setup using sqLite
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station


#################################################
# Flask Setup
#################################################

# Create an app, being sure to pass __name__
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Define what to do when a user hits the index route


#################################################
# Flask Routes
#################################################
# Home page
@app.route("/")
def home():
    return (
        f"Welcome to the Hawaii Climate API!<br/>"
        f"Available Routes:<br/>"
        f"Precipitation for last year in DB:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/api/v1.0/precipitation<br/>"
        f"List of Weather Stations:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/api/v1.0/stations<br/>"
        f"Temperature for one year:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/api/v1.0/tobs<br/>"
        f"Temperature stats start date (yyyy-mm-dd) ie (2017-08-01):&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/api/v1.0/&lt;start&gt;<br/>"
        f"Temperature stats start and end dates (yyyy-mm-dd) ie (2017-08-01/2017-08-05):&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/api/v1.0/&lt;start&gt;/&lt;end&gt;<br/>"
        f"About: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/about"
    )
####################
# Precipitation page
@app.route("/api/v1.0/precipitation")
def precipitation():
    print("Server received request for 'Precipitation' page...")
     # Create our session (link) from Python to the DB
    session = Session(engine)
    # Get the most recent date
    recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    dt_recent = dt.datetime.strptime(recent_date[0],'%Y-%m-%d')  
    dt_recent = dt.datetime.date(dt_recent)  #adjust so no time
    # calulat date oner year from latest date
    one_year_ago = dt_recent.replace(dt_recent.year - 1)

    # Perform a query to retrieve the data and precipitation scores
    m2_cols = (Measurement.date, Measurement.prcp)

    # Query for the dates and precipitation values for the last year in the database
    prcp_data = session.query(*m2_cols).\
            filter(Measurement.date >= one_year_ago.strftime('%Y-%m-%d')).\
            order_by(Measurement.date.desc()).all()
   

    session.close()

    # Convert to list of dictionaries to jsonify
    # use date as the key
    prcp_list = []
    # key, value
    for date, prcp in prcp_data:
        prcp_dict = {}
        prcp_dict[date] = prcp
        prcp_list.append(prcp_dict)

    return jsonify(prcp_list)

###############
# Stations page
# FLASK jsonify, orders alphabetically
@app.route("/api/v1.0/stations")
def stations():
    print("Server received request for 'Stations' page...")

    # Create our session (link) from Python to the DB
    session = Session(engine)

    sel_col = [Station.station,Station.name,Station.latitude,Station.longitude,Station.elevation]
    station_data = session.query(*sel_col).all()

    session.close()

    stations_list = []
    for station,name,lat,lon,el in station_data:
        station_dict={}
        station_dict['Station']=station
        station_dict["Name"] = name
        station_dict["Lat"] = lat
        station_dict["Lon"] = lon
        station_dict["Elevation"] = el

        stations_list.append(station_dict)


    return jsonify(stations_list)
    

###############################
# Temperature Observations page
@app.route("/api/v1.0/tobs")
def tobs():
    print("Server received request for 'tobs' page...")

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Get the most recent date
    recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    dt_recent = dt.datetime.strptime(recent_date[0],'%Y-%m-%d')  
    dt_recent = dt.datetime.date(dt_recent)  #adjust so no time
    
    # calulat date oner year from latest date
    one_year_ago = dt_recent.replace(dt_recent.year - 1)

    # Design a query to find the most active station
    counts_by_station =  session.query(Measurement.station, func.count(Measurement.station)).\
                    group_by(Measurement.station).\
                    order_by(func.count(Measurement.station).desc()).all()

    # Query for the dates and temperature values, of the most active station above, for the last year of data.
    temp_data_active_stn = session.query(Measurement.date,Measurement.tobs).\
                           filter(Measurement.station == counts_by_station[0][0]).\
                           filter(Measurement.date >= one_year_ago.strftime('%Y-%m-%d')).all()
                           

                         
    session.close() 

    # Convert to list of dictionaries to jsonify
    tobs_list = []

    for date, tobs in temp_data_active_stn:
        tobs_dict = {}
        tobs_dict[date] = tobs
        tobs_list.append(tobs_dict)

    return jsonify(tobs_list)
    
    
###################################################
# Temperature statistics page with start date input
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temp_stats_start(start=None, end=None):
    # tmin, tavg, tmax per date, starting from a starting date.
    # Args:
        # start (string): A date string in the format %Y-%m-%d
    # Returns:
        # tmin, tavg, and tmax

    print("Enter start date in url: ie(/2017-08-01)")
    # Create our session (link) from Python to the DB

    session = Session(engine)
    if not end:
        stats_temp_data= session.query(Measurement.date,\
                                func.min(Measurement.tobs), \
                                func.avg(Measurement.tobs), \
                                func.max(Measurement.tobs)).\
                                filter(Measurement.date >= start).\
                                group_by(Measurement.date).\
                                order_by(Measurement.date.desc()).all()
    else:
        stats_temp_data= session.query(Measurement.date,\
                            func.min(Measurement.tobs), \
                            func.avg(Measurement.tobs), \
                            func.max(Measurement.tobs)).\
                            filter(Measurement.date >= start).\
                            filter(Measurement.date <= end).\
                            group_by(Measurement.date).\
                            order_by(Measurement.date.desc()).all()
    session.close() 

    stats_temp_list = []

    for date, tmin, tavg, tmax in stats_temp_data:
        stat_dict = {}
        stat_dict["Date"] = date
        stat_dict["tmin"] = tmin
        stat_dict["tavg"] = tavg
        stat_dict["tmax"] = tmax
        stats_temp_list.append(stat_dict)

    
    return jsonify(stats_temp_list)
    

# Define what to do when a user hits the /about route
# About page
@app.route("/about")
def about():
    print("Server received request for 'About' page...")
    return "Weather data for Hawaii, rainfall in inches, and temperature in Fahrenheit, most recent date is 2017-08-23"




# runs the program

if __name__ == "__main__":
    app.run(debug=True)
