#!/usr/bin/env python

from flask import Flask, render_template, request, make_response, send_from_directory
import base64
import datetime
import requests
import json
import os

app = Flask(__name__)

stations = {
    "U": {"name": "Uppsala", "id": "cf09cbb1-fd82-4b83-9c09-87bc8fc2f018"},
    "Cst": {"name": "Stockholm", "id": "f4d25596-a9f9-41a1-b200-713439d92fc4"},
    "Srv": {"name": "Storvreta", "id": "ddf64ca1-b3b3-4820-94fb-137f17fbefc3"},
}


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
    r = requests.post(
        "https://evf-regionsormland.preciocloudapp.net/api/Claims",
        json=create_request_body(
            request.json.get("ticket"),
            request.json.get("from"),
            request.json.get("to"),
            request.json.get("departure"),
            request.json.get("customer"),
        ),
    )

    if r:
        resp = make_response("Request submitted!")

        return resp
    else:
        return f"Something went wrong submitting the request: {r.text}", 500


@app.route("/api/departures/<departure_station>/<arrival_station>/<date>", methods=["GET"])
def get_departures(departure_station, arrival_station, date):
    r = requests.get(
        "https://evf-regionsormland.preciocloudapp.net/api/TrainStations/GetDepartureTimeList",
        params={"departureStationId": departure_station, "arrivalStationId": arrival_station, "departureDate": date},
    )

    return r.text

def get_train_number(departure_station, arrival_station, departure_time):
    r = requests.get(
        "https://evf-regionsormland.preciocloudapp.net/api/TrainStations/GetDistance",
        params={"departureStationId": departure_station, "arrivalStationId": arrival_station, "departureDate": departure_time},
    )

    return r.json()["data"]["trafikverketTrainId"]



@app.route("/api/arrival_stations/<station>", methods=["GET"])
def get_arrival_stations(station):
    arrival_stations = {"U": ["Cst", "Srv"], "Cst": ["U"], "Srv": ["U"]}

    return {
        "stations": [
            {"name": x, "longname": stations[x]["name"]}
            for x in arrival_stations[station]
        ]
    }


def create_request_body(ticket, dep_station, arr_station, departure, customer):
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "customer": customer | {
            "id": "00000000-0000-0000-0000-000000000000",
            "bankAccountNumber": "",
            "clearingNumber": ""
        },
        "ticketNumber": ticket,
        "ticketType": 1,
        "departureStationId": stations[dep_station]["id"],
        "arrivalStationId": stations[arr_station]["id"],
        "departureDate": departure,
        "comment": "",
        "status": 0,
        "trainNumber": get_train_number(dep_station, arr_station, departure),
        "refundType": {
            "id": "00000000-0000-0000-0000-000000000000",
            "name": "Payment via Swedbank SUS",
        },
        "claimReceipts": [],
    }


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
