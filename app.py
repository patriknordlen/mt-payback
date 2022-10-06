#!/usr/bin/env python

from flask import Flask, render_template, request, make_response
import base64
import datetime
import requests
import json

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
            persons=get_customers(request.cookies.get("ticketholders")),
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


@app.route("/api/submit", methods=["POST"])
def submit():
    ticketholders = json.loads(
        base64.b64decode(request.cookies.get("ticketholders")).decode("latin-1")
    )

    r = requests.post(
        "https://evf-regionsormland.preciocloudapp.net/api/Claims",
        json=create_request_body(
            request.form.get("ticket"),
            request.form.get("from"),
            request.form.get("to"),
            request.form.get("departure"),
            request.form.get("ticketholder"),
        ),
    )

    if r:
        resp = make_response("Request submitted!")
        resp.set_cookie("ticketholder", request.form.get("ticketholder"))
        resp.set_cookie("expirydate", request.form.get("expirydate"))
        resp.set_cookie("ticket", request.form.get("ticket"))

        return resp
    else:
        return f"Something went wrong submitting the request: {r.text}"


@app.route("/api/departures/<station>/<date>", methods=["GET"])
def get_departures(station, date):
    r = requests.get(
        "https://evf-regionsormland.preciocloudapp.net/api/TrainStations/GetDepartureTimeList",
        params={"stationId": station, "departureDate": date},
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


def get_customers(ticketholders):
    if ticketholders:
        print(ticketholders)
        customers = json.loads(base64.b64decode(ticketholders).decode("latin-1"))
    else:
        customers = {}

    return customers


def get_customer_details(name):
    return get_customers()[name]


def create_request_body(ticket, dep_station, arr_station, departure, name):
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "customer": name,
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
