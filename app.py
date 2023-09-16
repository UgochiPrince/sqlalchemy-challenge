# Import the dependencies.
import datetime as dt
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session


#################################################
# Database Setup
#################################################


# reflect an existing database into a new model
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect the tables
Base = automap_base()
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


# Define a function to calculate temperature statistics
def calculate_temperature_stats(start_date, end_date=None):
    if end_date:
        temp_data = (
            session.query(
                func.min(Measurement.tobs).label("min_temperature"),
                func.avg(Measurement.tobs).label("avg_temperature"),
                func.max(Measurement.tobs).label("max_temperature"),
            )
            .filter(Measurement.date >= start_date, Measurement.date <= end_date)
            .first()
        )
    else:
        temp_data = (
            session.query(
                func.min(Measurement.tobs).label("min_temperature"),
                func.avg(Measurement.tobs).label("avg_temperature"),
                func.max(Measurement.tobs).label("max_temperature"),
            )
            .filter(Measurement.date >= start_date)
            .first()
        )

    return {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d") if end_date else None,
        "min_temperature": temp_data.min_temperature,
        "avg_temperature": temp_data.avg_temperature,
        "max_temperature": temp_data.max_temperature,
    }


#################################################
# Flask Routes
#################################################
# Define the homepage route
@app.route("/")
def home():
    return (
        "Welcome to the Climate App API!<br/><br/>"
        "Available Routes:<br/>"
        "/api/v1.0/precipitation - Precipitation data for the last 12 months<br/>"
        "/api/v1.0/stations - List of weather stations<br/>"
        "/api/v1.0/tobs - Temperature observations for the most active station (last 12 months)<br/>"
        "/api/v1.0/start_date - Minimum, average, and maximum temperatures for a given start date<br/>"
        "/api/v1.0/start_date/end_date - Minimum, average, and maximum temperatures for a date range<br/>"
    )


# Define the precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Calculate the date one year from the last date in the dataset
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = dt.datetime.strptime(most_recent_date, "%Y-%m-%d")
    one_year_ago = most_recent_date - dt.timedelta(days=365)

    # Query precipitation data for the last 12 months
    precipitation_data = (
        session.query(Measurement.date, Measurement.prcp)
        .filter(Measurement.date >= one_year_ago, Measurement.date <= most_recent_date)
        .all()
    )

    # Convert the query results to a list of dictionaries
    precip_list = [{"date": date, "prcp": prcp} for date, prcp in precipitation_data]

    # Return the data in JSON format
    return jsonify(precip_list)


# Define the stations route
@app.route("/api/v1.0/stations")
def stations():
    # Query all stations from the Station table
    stations_data = session.query(Station.station, Station.name).all()

    # Create a list of dictionaries containing station information
    station_list = [
        {"station": station, "name": name} for station, name in stations_data
    ]

    # Return the list of stations as JSON
    return jsonify(station_list)


# Define the temperature observations route
@app.route("/api/v1.0/tobs")
def tobs():
    # Calculate the date one year from the last date in the dataset
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = dt.datetime.strptime(most_recent_date, "%Y-%m-%d")
    one_year_ago = most_recent_date - dt.timedelta(days=365)

    # Query for the most active station based on tobs count
    most_active_station_data = (
        session.query(Measurement.station, func.count(Measurement.tobs))
        .filter(Measurement.date >= one_year_ago, Measurement.date <= most_recent_date)
        .group_by(Measurement.station)
        .order_by(func.count(Measurement.tobs).desc())
        .first()
    )

    # Extract the most active station ID from the query result
    most_active_station = most_active_station_data[0]

    # Query temperature observations for the most active station in the last 12 months
    tobs_data = (
        session.query(Measurement.date, Measurement.tobs)
        .filter(Measurement.station == most_active_station)
        .filter(Measurement.date >= one_year_ago, Measurement.date <= most_recent_date)
        .all()
    )

    # Create a list of temperature observations
    temperature_observations = [
        {"date": date, "temperature": temp} for date, temp in tobs_data
    ]

    # Return the JSON list of temperature observations
    return jsonify(temperature_observations)


# Define the start date route
@app.route("/api/v1.0/<start>")
def temp_start_date(start):
    start_date = dt.datetime.strptime(start, "%Y-%m-%d")
    temperature_stats = calculate_temperature_stats(start_date)
    return jsonify(temperature_stats)


# Define the start date and end date route
@app.route("/api/v1.0/<start>/<end>")
def temp_start_end_date(start, end):
    start_date = dt.datetime.strptime(start, "%Y-%m-%d")
    end_date = dt.datetime.strptime(end, "%Y-%m-%d")
    temperature_stats = calculate_temperature_stats(start_date, end_date)
    return jsonify(temperature_stats)


if __name__ == "__main__":
    app.run(debug=True)
