#!/usr/bin/env python

from flask import Flask, render_template, request
import datetime
import requests
import jsonstore
import json

app = Flask(__name__)
store = jsonstore.JsonStore("mt-payback.json")

stations = {
    "U": {"name": "Uppsala", "id": "cf09cbb1-fd82-4b83-9c09-87bc8fc2f018"},
    "Cst": {"name": "Stockholm", "id": "f4d25596-a9f9-41a1-b200-713439d92fc4"},
    "Srv": {"name": "Storvreta", "id": "ddf64ca1-b3b3-4820-94fb-137f17fbefc3"},
}


@app.route("/", methods=["GET"])
def index():
    if (
        store.get("expirydate") == None
        or datetime.datetime.strptime(store.get("expirydate"), "%Y-%m-%d").date()
        < datetime.date.today()
    ):
        store.unset("expirydate")
        store.unset("ticketholder")
        store.unset("ticket")

    return render_template("main.html", today=datetime.date.today(), **store.get_all())


@app.route("/api/submit", methods=["POST"])
def submit():
    store.set_all(request.form.to_dict())

    r = requests.post(
        "https://evf-regionsormland.preciocloudapp.net/api/Claims",
        json=create_request_body(
            request.form.get("ticket"),
            request.form.get("from"),
            request.form.get("to"),
            request.form.get("departure"),
            request.form.get("ticketholder"),
        ),
        verify=False,
    )

    if r:
        return "Request submitted!"
    else:
        return f"Something went wrong submitting the request: {r.text}"


@app.route("/api/departures/<station>/<date>", methods=["GET"])
def get_departures(station, date):
    r = requests.get(
        "https://evf-regionsormland.preciocloudapp.net/api/TrainStations/GetDepartureTimeList",
        params={"stationId": station, "departureDate": date},
        verify=False,
    )

    return r.text


@app.route("/api/arrival_stations/<station>", methods=["GET"])
def get_arrival_stations(station):
    arrival_stations = {"U": ["Cst", "Srv"], "Cst": ["U"], "Srv": ["U"]}

    return {
        "stations": [
            {"name": x, "longname": stations[x]["name"]}
            for x in arrival_stations[station]
        ]
    }


def get_customer_details(name):
    with open("ticketholders.json") as f:
        customers = json.load(f)

    return customers[name]


def create_request_body(ticket, dep_station, arr_station, departure, name):
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "customer": get_customer_details(name),
        "ticketNumber": ticket,
        "ticketType": 1,
        "departureStationId": stations[dep_station]["id"],
        "arrivalStationId": stations[arr_station]["id"],
        "departureDate": departure,
        "comment": "",
        "status": 0,
        "trainNumber": 0,
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
