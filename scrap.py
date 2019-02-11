import json

import AdvancedHTMLParser
import matplotlib.pyplot as plt
import openflights

from numpy import concatenate
from numpy import linspace
from scipy.interpolate import interp1d
from model import *

parser = AdvancedHTMLParser.AdvancedHTMLParser()

SCRAP_ROOT = "scrap/"
PLANES_PATH = SCRAP_ROOT + "planes/"
NETWORK_PATH = SCRAP_ROOT + "network/"
NEWLINE_PATH = SCRAP_ROOT + "newline/"
MARKETING_PATH = SCRAP_ROOT + "marketing/"
JSON_PATH = SCRAP_ROOT + "json/"

NEWLINES = ["thailand.html", "india.html", "singapore.html", "taiwan.html", "vietnam.html"]


class HTML:
    planes = {}
    airports = {}
    lines = {}
    newlines = {}

    market_index = {Market.eco.name: 0, Market.biz.name: 0, Market.pre.name: 0}
    market_key = {Market.eco.name: "paxAttEco", Market.biz.name: "paxAttBus", Market.pre.name: "paxAttFirst"}
    price_per_km = None

    @classmethod
    def read(cls):
        cls._read_planes()
        cls._read_hubs()
        cls._read_lines()
        cls._read_newlines()

    @classmethod
    def write(cls):
        if cls.planes == {} or cls.airports == {}:
            cls.read()

        JSON.planes = cls.planes
        JSON.airports = cls.airports
        JSON.lines = HTML.lines
        for hub_iata, hub in HTML.newlines.items():
            for dst_iata, line in hub.items():
                try:
                    JSON.lines[hub_iata][dst_iata] = line
                except KeyError:
                    JSON.lines[hub_iata] = {dst_iata: line}
        JSON.write()

    @classmethod
    def _read_hubs(cls):
        hub_filenames = ["hub.html"]
        for filename in hub_filenames:
            parser.parseFile(NETWORK_PATH + filename)
            tax = cls._hub_scrap()
            iata, lon, lat = cls._map_network_json_scrap()
            try:
                hub = openflights.airports[iata]
                hub.tax = tax
            except KeyError:
                hub = Airport(lat=lat, lon=lon, tax=tax, iata=iata)

            cls.airports[hub.iata] = hub

    @classmethod
    def _read_lines(cls):
        plane_page_attributes = cls._lines_attributes_from_planes_page()

        cls.lines.clear()

        for line_id, line_attrib in plane_page_attributes.items():
            tax, country, name = cls._network_scrap(line_id)
            ticket_price, distance, demand = cls._marketing_scrap(line_id, line_attrib)
            hub_iata, hub_lon, hub_lat, dst_iata, dst_lat, dst_lon = cls._map_network_json_scrap()
            try:
                airport = openflights.airports[dst_iata]
                airport.tax = tax
            except KeyError:
                airport = Airport(dst_lat, dst_lon, tax=tax, iata=dst_iata, name=name,
                                  loc={"country": country, "city": None, "tmz": None})

            cls.airports[airport.iata] = airport
            line = Line(cls.airports[hub_iata], cls.airports[dst_iata], demand, ticket_price, distance)
            try:
                cls.lines[hub_iata][dst_iata] = line
            except KeyError:
                cls.lines[hub_iata] = {dst_iata: line}

        cls.price_per_km = cls._base_price_function()

    @classmethod
    def _read_newlines(cls):
        cls.newlines.clear()
        for filename in NEWLINES:
            parser.parseFile(NEWLINE_PATH + filename)
            hub_iata = parser.getElementsByClassName("hubNameBox")[0].innerText.split(" -  -")[0].split(" ")[-1]
            airport_elems = parser.getElementsByClassName("airportList")[0]
            airport_elems = concatenate([airport_elems.getElementsByClassName("greenOutline"),
                                         airport_elems.getElementsByClassName("yellowOutline")])
            for airport in airport_elems:
                dst_iata, tax, demand, ticket_price, distance, price = cls._newline_scrap(airport)
                try:
                    airport = openflights.airports[dst_iata]
                    airport.tax = tax
                except KeyError:
                    airport = Airport(0, 0, tax=tax, iata=dst_iata, price=price)

                cls.airports[dst_iata] = airport
                line = Line(cls.airports[hub_iata], cls.airports[airport.iata], demand, ticket_price, distance, True)
                try:
                    cls.newlines[hub_iata][dst_iata] = line
                except KeyError:
                    cls.newlines[hub_iata] = {dst_iata: line}

    @classmethod
    def _read_planes(cls):
        filenames = [PLANES_PATH + "short_range.html", PLANES_PATH + "middle_range.html",
                     PLANES_PATH + "long_range.html"]

        cls.planes.clear()
        for name in filenames:
            parser.parseFile(name)
            planes_elem = parser.getElementsByClassName("aircraftList")
            for plane in planes_elem[0].getChildren():
                name, price, speed, pax, year, max_range, cons, wear_rate, pax_dict = cls._planes_scrap(plane)
                cls.planes[name] = Plane(name, pax_dict, speed, cons, year, max_range, price, wear_rate)

    @classmethod
    def _base_price_function(cls, plot_interpolation_data=False):
        sorted_lines = []
        for h in cls.lines.values():
            sorted_lines.extend(h.values())

        sorted_lines = sorted(sorted_lines, key=lambda x: x.distance)

        x_num = {m.name: list(map(lambda x: x.ticket_price[m.name], sorted_lines)) for m in Market}
        x_den = list(map(lambda x: x.distance, sorted_lines))

        y = {}
        for m in Market:
            y[m.name] = []
            for k in range(0, len(x_den)):
                y[m.name].append(x_num[m.name][k] / x_den[k])

        x_interp = linspace(400, 2000, 4096)

        base_price_function = {}
        for m in Market:
            base_price_function[m.name] = interp1d(x_den, y[m.name], kind="quadratic", fill_value="extrapolate")
            if plot_interpolation_data:
                plt.plot(x_den, y[m], 'o', x_interp, base_price_function[m](x_interp), '--')
                plt.title("Price/Distance " + m.value)
                plt.show()
        return base_price_function

    @classmethod
    def _lines_attributes_from_planes_page(cls):
        parser.parseFile(PLANES_PATH + "middle_range.html")
        json_str = str(parser.getElementById("lineListJson").innerHTML) \
            .replace("\n", "").replace("\\/", "").replace(" ", "").replace("HYD", "")
        return json.loads(json_str)

    @classmethod
    def _network_scrap(cls, line_id):
        parser.parseFile(NETWORK_PATH + line_id + ".html")
        box1_children = parser.getElementById("box1").getChildren()
        box2_children = parser.getElementById("box2").getChildren()

        tax = float(box1_children[2].getChildren()[0].innerText.replace(" ", "").replace("$", ""))
        country = box2_children[3].getChildren()[0].innerText.split(" /  ")[1]
        name = parser.getElementsByClassName("lineTitle")[0].innerText.split("\n")[-2].split(" -  - ")[1]

        return tax, country, name

    @classmethod
    def _marketing_scrap(cls, line_id, line_attrib):
        parser.parseFile(MARKETING_PATH + line_id + ".html")

        marketing_elem = parser.getElementById("marketing_linePricing").getElementsByClassName("box1")[0]
        price_boxes = marketing_elem.getElementsByClassName("priceBox")

        ticket_price = {key: price_boxes[i].getElementsByClassName("price")[0].getChildren()[0] for key, i in
                        cls.market_index.items()}
        ticket_price = {m.name: float(ticket_price[m.name].innerText.replace("$", "").replace("\xa0", "")) for m in
                        Market}

        distance = line_attrib["distance"]

        demand = {key: line_attrib[val] for key, val in cls.market_key.items()}

        return ticket_price, distance, demand

    @classmethod
    def _map_network_json_scrap(cls):
        map_network_json = json.loads(parser.getElementById('map_NetworkJson').innerText)
        hub_iata = map_network_json["airports"][0]["iata"]
        hub_lat = map_network_json["airports"][0]["latitude"]
        hub_lon = map_network_json["airports"][0]["longitude"]
        try:
            dst_iata = map_network_json["airports"][1]["iata"]
            dst_lat = map_network_json["airports"][1]["latitude"]
            dst_lon = map_network_json["airports"][1]["longitude"]
        except IndexError:
            return hub_iata, hub_lon, hub_lat

        return hub_iata, hub_lon, hub_lat, dst_iata, dst_lat, dst_lon

    @classmethod
    def _newline_scrap(cls, airport_elem):
        content = airport_elem.getElementsByClassName("hubCategoryBox")[0]
        demand_elem = airport_elem.getElementsByClassName("demand")[0].getChildren()

        dst_iata = airport_elem.getElementsByClassName("hubNameBox")[0].innerText.split()[0]
        distance = float(
            content.getElementsByClassName("lineDistance")[0].innerText.replace("km", "").replace(" ", ""))
        tax = float(
            content.getChildren()[3].getChildren()[0].innerHTML.replace("&nbsp;", "").replace("$/vol", ""))

        demand = {
            Market.eco.name: float(demand_elem[1].getChildren()[1].innerHTML.split()[-1]),
            Market.biz.name: float(demand_elem[2].getChildren()[1].innerHTML.split()[-1]),
            Market.pre.name: float(demand_elem[3].getChildren()[1].innerHTML.split()[-1])
        }

        price = float(
            airport_elem.getElementsByClassName("priceBox")[0].getChildren()[3].innerText.replace("&nbsp;", "").replace(
                "$", "").split(": ")[-1])

        ticket_price = {m.name: distance * cls.price_per_km[m.name](distance) for m in Market}

        return dst_iata, tax, demand, ticket_price, distance, price

    @classmethod
    def _planes_scrap(cls, plane_elem):
        infos_elem = plane_elem.getElementsByClassName("aircraftInfo")[0]
        price_elem = plane_elem.getElementsByClassName("aircraftPrice")[0].getChildren()

        list_elem = infos_elem.getChildren()[1]
        list_elem_bis = infos_elem.getChildren()[2]
        price_elem_div = price_elem[2].getChildren()[1]

        name = str(price_elem[1].getAttribute("value"))
        price = float(price_elem_div.getChildren()[1].getAttribute("value"))

        speed = float(list_elem_bis.getChildren()[1].getChildren()[0].innerText.replace("km/h", ""))
        pax = float(list_elem_bis.getChildren()[0].getChildren()[0].innerText)

        year = int(list_elem.getChildren()[0].getChildren()[0].innerText)
        max_range = float(list_elem.getChildren()[1].getChildren()[0].innerText.replace("km", "").replace(" ", ""))
        cons = float(list_elem.getChildren()[2].getChildren()[0].innerText.replace("L/100km/pax", ""))
        wear_rate = float(list_elem.getChildren()[3].getChildren()[0].innerText.replace("%/100h", "")) / 100.
        pax_dict = {Market.eco.name: pax, Market.biz.name: 0, Market.pre.name: 0}

        return name, price, speed, pax, year, max_range, cons, wear_rate, pax_dict

    @classmethod
    def _hub_scrap(cls):
        box2 = parser.getElementById("box2")
        tax = float(box2.getChildren()[3].getChildren()[0].innerText.replace("\xa0", "").replace("$", ""))
        return tax


class JSON:
    planes = {}
    airports = {}
    lines = {}

    @classmethod
    def read(cls):
        cls._read_planes()
        cls._read_airports()
        cls._read_lines()

    @classmethod
    def write(cls):
        cls._write_planes()
        cls._write_airports()
        cls._write_lines()

    @classmethod
    def _read_planes(cls, filename="planes.json"):
        cls.planes.clear()
        with open(JSON_PATH + filename, "r") as json_file:
            planes_json = json.load(json_file)

        for plane_json in planes_json:
            cls.planes[plane_json["name"]] = Plane.from_dict(plane_json)

    @classmethod
    def _read_airports(cls, filename="airports.json"):
        cls.airports.clear()
        with open(JSON_PATH + filename, "r") as json_file:
            airports_json = json.load(json_file)

        for airport_json in airports_json:
            cls.airports[airport_json["iata"]] = Airport.from_dict(airport_json)

    @classmethod
    def _read_lines(cls, filename="lines.json"):
        cls.lines.clear()
        with open(JSON_PATH + filename, "r") as json_file:
            lines_json = json.load(json_file)

        for line_json in lines_json:
            line = Line.from_dict(line_json, cls.airports[line_json["hub"]], cls.airports[line_json["dst"]])
            try:
                cls.lines[line_json["hub"]][line_json["dst"]] = line
            except KeyError:
                cls.lines[line_json["hub"]] = {line_json["dst"]: line}

    @classmethod
    def _write_planes(cls, filename="planes.json"):
        planes_json = []
        for plane in cls.planes.values():
            planes_json.append(plane.__dict__)

        with open(JSON_PATH + filename, "w") as json_file:
            json.dump(planes_json, json_file, indent=4)

    @classmethod
    def _write_airports(cls, filename="airports.json"):
        airports_json = []
        for airport in cls.airports.values():
            airports_json.append(airport.__dict__)

        with open(JSON_PATH + filename, "w") as json_file:
            json.dump(airports_json, json_file, indent=4)

    @classmethod
    def _write_lines(cls, filename="lines.json"):
        lines_json = []
        for hub in cls.lines.values():
            for line in hub.values():
                lines_json.append(line.__dict__())

        with open(JSON_PATH + filename, "w") as json_file:
            json.dump(lines_json, json_file, indent=4)


JSON.read()

print("Scrap JSON data successfully loaded from " + JSON_PATH)