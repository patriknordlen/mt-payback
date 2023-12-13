#!/usr/bin/env python

from flask import (
    Flask,
    render_template,
    request,
    make_response,
    send_from_directory,
    jsonify,
)
import datetime
import requests
import operators

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    resp = make_response(
        render_template(
            "main.html",
            today=datetime.date.today(),
            **request.cookies,
        )
    )

    if (
        request.cookies.get("expirydate") == None
        or datetime.datetime.strptime(
            request.cookies.get("expirydate"), "%Y-%m-%d"
        ).date()
        < datetime.date.today()
    ):
        resp.delete_cookie("expirydate")
        resp.delete_cookie("ticketholder")
        resp.delete_cookie("ticket")

    return resp


@app.route("/static/<path:path>")
def send_static_file(path):
    return send_from_directory("static", path)


@app.route("/api/submit", methods=["POST"])
def submit():
    operator = request.json.get("operator")
    if operator == "sj":
        op = operators.SJ()
    elif operator == "mt":
        op = operators.MT()

    r = op.submit(
        request.json.get("ticket"),
        request.json.get("from"),
        request.json.get("to"),
        request.json.get("departureDate"),
        request.json.get("departureTime"),
        request.json.get("customer"),
    )

    if r:
        resp = make_response("Request submitted!")

        return resp
    else:
        return f"Something went wrong submitting the request: {r.text}", 500


@app.route(
    "/api/departures/<departure_station>/<arrival_station>/<date>", methods=["GET"]
)
def get_departures(departure_station, arrival_station, date):
    r = requests.get(
        "https://evf-regionsormland.preciocloudapp.net/api/TrainStations/GetDepartureTimeList",
        params={
            "departureStationId": departure_station,
            "arrivalStationId": arrival_station,
            "departureDate": date,
        },
    )

    return jsonify(sorted(r.json()["data"]))


def get_train_number(departure_station, arrival_station, departure_time):
    r = requests.get(
        "https://evf-regionsormland.preciocloudapp.net/api/TrainStations/GetDistance",
        params={
            "departureStationId": departure_station,
            "arrivalStationId": arrival_station,
            "departureDate": departure_time,
        },
    )

    return r.json()["data"]["trafikverketTrainId"]


@app.route("/api/arrival_stations/<station>", methods=["GET"])
def get_arrival_stations(station):
    arrival_stations = {
        "U": ["Cst", "Srv", "Fvk", "Gä"],
        "Cst": ["U"],
        "Srv": ["U", "Fvk", "Gä"],
    }

    station_names = {
        "U": "Uppsala C",
        "Cst": "Stockholm C",
        "Srv": "Storvreta",
        "Fvk": "Furuvik",
        "Gä": "Gävle",
    }

    return {
        "stations": [
            {"name": x, "longname": station_names[x]} for x in arrival_stations[station]
        ]
    }


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
