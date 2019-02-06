import json

import AdvancedHTMLParser
import matplotlib.pyplot as plt
import openflights

from numpy import concatenate
from numpy import linspace
from scipy.interpolate import interp1d

from Market import Market
from Airport import Airport
from Line import Line
from Plane import Plane

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
    lines = []
    newlines = []

    @classmethod
    def _base_price_function(cls, plot_interpolation_data=False):
        sorted_lines = sorted(cls.lines, key=lambda x: x.distance)

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
    def hub_data(cls):
        parser.parseFile(NETWORK_PATH + "hub.html")
        map_network_json = json.loads(parser.getElementById('map_NetworkJson').innerText)
        box2 = parser.getElementById("box2")
        tax = float(box2.getChildren()[3].getChildren()[0].innerText.replace("\xa0", "").replace("$", ""))
        iata = map_network_json["airports"][0]["iata"]
        hub = openflights.airports[iata]
        hub.tax = tax
        cls.airports[hub.iata] = hub
        return hub.iata

    @classmethod
    def lines_data(cls):
        plane_page_attributes = cls._lines_attributes_from_planes_page()
        market_index = {Market.eco.name: 0, Market.biz.name: 0, Market.pre.name: 0}
        market_key = {Market.eco.name: "paxAttEco", Market.biz.name: "paxAttBus", Market.pre.name: "paxAttFirst"}

        cls.airports.clear()
        cls.lines.clear()
        hub_iata = cls.hub_data()
        for line_key, line_attrib in plane_page_attributes.items():
            parser.parseFile(NETWORK_PATH + line_key + ".html")
            tax = float(
                parser.getElementById("box1").getChildren()[2].getChildren()[0].innerText.replace(" ", "").replace("$",
                                                                                                                   ""))

            parser.parseFile(MARKETING_PATH + line_key + ".html")

            marketing_elem = parser.getElementById("marketing_linePricing").getElementsByClassName("box1")[0]
            price_boxes = marketing_elem.getElementsByClassName("priceBox")

            ticket_price = {key: price_boxes[i].getElementsByClassName("price")[0].getChildren()[0] for key, i in
                            market_index.items()}
            ticket_price = {m.name: float(ticket_price[m.name].innerText.replace("$", "").replace("\xa0", "")) for m in
                            Market}

            distance = line_attrib["distance"]

            demand = {key: line_attrib[val] for key, val in market_key.items()}

            map_network_json = json.loads(parser.getElementById('map_NetworkJson').innerText)
            iata = map_network_json["airports"][1]["iata"]
            try:
                airport = openflights.airports[iata]
                airport.tax = tax
            except KeyError:
                lat = map_network_json["airports"][1]["latitude"]
                lon = map_network_json["airports"][1]["longitude"]
                airport = Airport(lat, lon, tax=tax, iata=iata)

            cls.airports[airport.iata] = airport
            cls.lines.append(Line(cls.airports[hub_iata], cls.airports[airport.iata], demand, ticket_price, distance))

    @classmethod
    def newlines_data(cls, lines):
        hub = cls.hub_data()
        airports = []
        base_price_per_km = cls._base_price_function(lines)
        newlines = []
        for filename in NEWLINES:
            parser.parseFile(NEWLINE_PATH + filename)
            airport_list_elem = parser.getElementsByClassName("airportList")[0]
            airport_list_elem = concatenate([airport_list_elem.getElementsByClassName("greenOutline"),
                                             airport_list_elem.getElementsByClassName("yellowOutline")])
            for airport in airport_list_elem:
                content = airport.getElementsByClassName("hubCategoryBox")[0]
                demand_elem = airport.getElementsByClassName("demand")[0].getChildren()

                iata = airport.getElementsByClassName("hubNameBox")[0].innerText.split()[0]
                distance = float(
                    content.getElementsByClassName("lineDistance")[0].innerText.replace("km", "").replace(" ", ""))
                tax = float(
                    content.getChildren()[3].getChildren()[0].innerHTML.replace("&nbsp;", "").replace("$/vol", ""))

                demand = {
                    Market.eco.name: float(demand_elem[1].getChildren()[1].innerHTML.split()[-1]),
                    Market.biz.name: float(demand_elem[2].getChildren()[1].innerHTML.split()[-1]),
                    Market.pre.name: float(demand_elem[3].getChildren()[1].innerHTML.split()[-1])
                }

                ticket_price = {m.name: distance * base_price_per_km[m.name](distance) for m in Market}

                try:
                    airport = openflights.airports[iata]
                    airport.tax = tax
                except KeyError:
                    airport = Airport(0, 0, tax=tax, iata=iata)

                airports.append(airport)
                newlines.append(Line(hub, airports[-1], demand, ticket_price, distance, True))

        return newlines, airports

    @classmethod
    def planes_data(cls):
        filenames = [PLANES_PATH + "short_range.html", PLANES_PATH + "middle_range.html",
                     PLANES_PATH + "long_range.html"]

        cls.planes.clear()
        for name in filenames:
            parser.parseFile(name)
            planes_elem = parser.getElementsByClassName("aircraftList")
            for plane in planes_elem[0].getChildren():
                infos_elem = plane.getElementsByClassName("aircraftInfo")[0]
                price_elem = plane.getElementsByClassName("aircraftPrice")[0].getChildren()

                list_elem = infos_elem.getChildren()[1]
                list_elem_bis = infos_elem.getChildren()[2]
                price_elem_div = price_elem[2].getChildren()[1]

                name = str(price_elem[1].getAttribute("value"))
                price = float(price_elem_div.getChildren()[1].getAttribute("value"))

                speed = float(list_elem_bis.getChildren()[1].getChildren()[0].innerText.replace("km/h", ""))
                pax = float(list_elem_bis.getChildren()[0].getChildren()[0].innerText)

                year = int(list_elem.getChildren()[0].getChildren()[0].innerText)
                max_range = float(
                    list_elem.getChildren()[1].getChildren()[0].innerText.replace("km", "").replace(" ", ""))
                cons = float(list_elem.getChildren()[2].getChildren()[0].innerText.replace("L/100km/pax", ""))
                wear_rate = float(list_elem.getChildren()[3].getChildren()[0].innerText.replace("%/100h", "")) / 100.
                pax_dict = {Market.eco.name: pax, Market.biz.name: 0, Market.pre.name: 0}

                cls.planes[name] = Plane(name, pax_dict, speed, cons, year, max_range, price, wear_rate)


class JSON:
    planes = {}
    airports = {}
    lines = {}
    newlines = []

    @classmethod
    def planes_data(cls, filename="planes.json"):
        cls.planes.clear()
        with open(JSON_PATH + filename, "r") as json_file:
            planes_json = json.load(json_file)

        for plane_json in planes_json:
            cls.planes[plane_json["name"]] = Plane.from_dict(plane_json)

    @classmethod
    def airports_data(cls, filename="airports.json"):
        cls.airports.clear()
        with open(JSON_PATH + filename, "r") as json_file:
            airports_json = json.load(json_file)

        for airport_json in airports_json:
            cls.airports[airport_json["iata"]] = Airport.from_dict(airport_json)

    @classmethod
    def lines_data(cls, filename="lines.json"):
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
    def write_planes(cls, filename="planes.json"):
        planes_json = []
        for plane in cls.planes.values():
            planes_json.append(plane.__dict__)

        with open(JSON_PATH + filename, "w") as json_file:
            json.dump(planes_json, json_file, indent=4)

    @classmethod
    def write_airports(cls, filename="airports.json"):
        airports_json = []
        for airport in cls.airports.values():
            airports_json.append(airport.__dict__)

        with open(JSON_PATH + filename, "w") as json_file:
            json.dump(airports_json, json_file, indent=4)

    @classmethod
    def write_lines(cls, filename="lines.json"):
        lines_json = []
        for hub in cls.lines.values():
            for line in hub.values():
                lines_json.append(line.__dict__())

        with open(JSON_PATH + filename, "w") as json_file:
            json.dump(lines_json, json_file, indent=4)


JSON.airports_data()
JSON.lines_data()
JSON.planes_data()

JSON.write_lines()
JSON.write_airports()
JSON.write_planes()

print("Scrap data successfully loaded from " + JSON_PATH)

# newlines, newairports = HTML.newlines_data(lines)
