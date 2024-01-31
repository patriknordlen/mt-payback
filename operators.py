import requests
import json


class MT:
    def __init__(self):
        self.stations = {
            "U": {"name": "Uppsala C", "id": "cf09cbb1-fd82-4b83-9c09-87bc8fc2f018"},
            "Cst": {
                "name": "Stockholm C",
                "id": "f4d25596-a9f9-41a1-b200-713439d92fc4",
            },
            "Srv": {"name": "Storvreta", "id": "ddf64ca1-b3b3-4820-94fb-137f17fbefc3"},
            "Fvk": {"name": "Furuvik", "id": "8751e52c-2214-4c1d-b64b-1d3eefc524b9"},
            "Gä": {"name": "Gävle", "id": "c1ed2e95-5cc2-4e9d-a89b-fb27f01ad527"},
            "Kn": {"name": "Knivsta", "id": "18df975c-61be-4029-94cd-fc565b0da4d9"},
            "Mr": {"name": "Märsta", "id": "57d62e84-ab78-437f-bd59-7e5839de3ce4"},
        }

    def submit(
        self, ticket, from_station, to_station, departure_date, departure_time, customer
    ):
        r = requests.post(
            "https://evf-regionsormland.preciocloudapp.net/api/Claims",
            json=self._create_request_body(
                ticket,
                from_station,
                to_station,
                self._get_fake_iso_string(departure_date, departure_time),
                customer,
            )
        )

        return True

    def _create_request_body(
        self, ticket, dep_station, arr_station, departure, customer
    ):
        return {
            "id": "00000000-0000-0000-0000-000000000000",
            "customer": customer
            | {
                "id": "00000000-0000-0000-0000-000000000000",
                "bankAccountNumber": "",
                "clearingNumber": "",
            },
            "ticketNumber": ticket,
            "ticketType": 1,
            "departureStationId": self.stations[dep_station]["id"],
            "arrivalStationId": self.stations[arr_station]["id"],
            "departureDate": departure,
            "comment": "",
            "status": 0,
            "trainNumber": self._get_train_number(dep_station, arr_station, departure),
            "refundType": {
                "id": "00000000-0000-0000-0000-000000000000",
                "name": "Payment via Swedbank SUS",
            },
            "claimReceipts": [],
        }

    def _get_train_number(self, departure_station, arrival_station, departure_time):
        r = requests.get(
            "https://evf-regionsormland.preciocloudapp.net/api/TrainStations/GetDistance",
            params={
                "departureStationId": departure_station,
                "arrivalStationId": arrival_station,
                "departureDate": departure_time,
            },
        )

        return r.json()["data"]["trafikverketTrainId"]

    def _get_fake_iso_string(self, departure_date, departure_time):
        return f"{departure_date}T{departure_time}.000Z"


class SJ:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
            }
        )
        self.stations = {
            "U": {"name": "Uppsala C", "id": "00005:074"},
            "Cst": {"name": "Stockholm Central", "id": "00001:074"},
            "Kn": {"name": "Knivsta", "id": "00559:074"},
            "Mr": {"name": "Märsta", "id": "00027:074"},
        }

    def submit(
        self, ticket, from_station, to_station, departure_date, departure_time, customer
    ):
        self._get_initial_cookies()
        self._register_ticket(ticket)
        self._add_travel_details(
            from_station, to_station, departure_date, departure_time
        )
        self._add_traveller_details(customer)
        self._add_payout_details(customer["identityNumber"], customer["mobileNumber"])

        return self._confirm()

    def _get_initial_cookies(self):
        self.session.get("https://www.sj.se/ersattning-vid-forsening")
        r = self.session.get("https://www.sj.se/cms/configuration")
        self.session.cookies.update(
            {x["name"]: x["token"] for x in r.json()["cookie"].values()}
        )

    def _register_ticket(self, ticket):
        r = self.session.post(
            "https://www.sj.se/v19/rest/compensation/delaycompensationtokens",
            data=json.dumps(
                {
                    "commuterCardType": "Movingo 30 dgr på SJ kort",
                    "commuterCardNumber": ticket,
                },
                ensure_ascii=False,
            ).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=UTF-8"},
        )
        self.token = r.json()["delayCompensationToken"]

    def _add_travel_details(
        self, from_station, to_station, departure_date, departure_time
    ):
        r = self.session.put(
            f"https://www.sj.se/v19/rest/compensation/{self.token}/traveldetails",
            files={
                "file": (
                    "data",
                    json.dumps(
                        {
                            "journeyDetail": {
                                "departureLocation": self.stations[from_station],
                                "arrivalLocation": self.stations[to_station],
                                "journeyDate": {"date": departure_date},
                                "journeyTime": {"time": departure_time[:5]},
                            },
                            "expenses": [],
                        },
                        ensure_ascii=False,
                    ).encode("utf-8"),
                    "application/json",
                )
            },
        )
        self.token = r.json()["delayCompensationToken"]

    def _add_traveller_details(self, customer):
        r = self.session.put(
            f"https://www.sj.se/v19/rest/compensation/{self.token}/contactinformation",
            data=json.dumps(
                {
                    "emailAddress": customer["email"],
                    "mobilePhoneNumber": customer["mobileNumber"].replace("-", ""),
                    "personName": {
                        "firstName": customer["firstName"],
                        "lastName": customer["surName"],
                    },
                    "personalIdentityNumber": customer["identityNumber"],
                },
                ensure_ascii=False,
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        self.token = r.json()["delayCompensationToken"]

    def _add_payout_details(self, ssn, mobileNumber):
        r = self.session.post(
            "https://www.sj.se/v19/rest/compensation/bankaccountrecords",
            json={
                "personalIdentityNumber": ssn,
                "swishPhoneNumber": mobileNumber.replace("-", ""),
            },
        )
        self.bar_id = r.json()["barId"]

    def _confirm(self):
        r = self.session.post(
            f"https://www.sj.se/v19/rest/compensation/{self.token}/confirmations",
            json={"paynovaBarIds": {"ticketCompensation": self.bar_id}},
        )
        return r
