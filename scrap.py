import json

import AdvancedHTMLParser
import matplotlib.pyplot as plt
from numpy import concatenate
from numpy import linspace
from scipy.interpolate import interp1d

from Hub import Hub
from Line import Line
from Plane import Plane

parser = AdvancedHTMLParser.AdvancedHTMLParser()

hubs = [
    Hub(tax=4497.0)
]

plot_interpolation_data = False

market = ["eco", "biz", "pre"]

SCRAP_ROOT = "scrap/"
PLANES_PATH = SCRAP_ROOT + "planes/"
NETWORK_PATH = SCRAP_ROOT + "network/"
NEwLINE_PATH = SCRAP_ROOT + "newline/"
MARKETING_PATH = SCRAP_ROOT + "marketing/"

NEWLINES = ["thailand.html", "india.html", "singapour.html", "taiwan.html", "vietnam.html"]


def _base_price_function(lines):
    sorted_lines = sorted(lines, key=lambda x: x.distance)

    x_num = {}
    for m in market:
        x_num[m] = list(map(lambda x: x.ticket_price[m], sorted_lines))

    x_den = list(map(lambda x: x.distance, sorted_lines))

    y = {}
    for m in market:
        y[m] = []
        for k in range(0, len(x_den)):
            y[m].append(x_num[m][k] / x_den[k])

    x_interp = linspace(400, 2000, 4096)

    base_price_function = {}
    for m in market:
        base_price_function[m] = interp1d(x_den, y[m], kind="quadratic", fill_value="extrapolate")
        if plot_interpolation_data:
            plt.plot(x_den, y[m], 'o', x_interp, base_price_function[m](x_interp), '--')
            plt.title("Price/Distance " + m)
            plt.show()
    return base_price_function


def _lines_attributes_from_planes_page():
    parser.parseFile(PLANES_PATH + "middle_range.html")
    json_str = str(parser.getElementById("lineListJson").innerHTML) \
        .replace("\n", "").replace("\\/", "").replace(" ", "").replace("HYD", "")
    return json.loads(json_str)


def lines_data():
    lines = []
    plane_page_attributes = _lines_attributes_from_planes_page()
    for line_key, line_attrib in plane_page_attributes.items():
        parser.parseFile(NETWORK_PATH + line_key + ".html")
        tax = float(
            parser.getElementById("box1").getChildren()[2].getChildren()[0].innerText.replace(" ", "").replace("$", ""))

        parser.parseFile(MARKETING_PATH + line_key + ".html")

        marketing_elem = parser.getElementById("marketing_linePricing").getElementsByClassName("box1")[0]
        price_boxes = marketing_elem.getElementsByClassName("priceBox")

        ticket_price = {
            "eco": price_boxes[0].getElementsByClassName("price")[0].getChildren()[0],
            "biz": price_boxes[1].getElementsByClassName("price")[0].getChildren()[0],
            "pre": price_boxes[2].getElementsByClassName("price")[0].getChildren()[0]
        }

        for m in market:
            ticket_price[m] = float(ticket_price[m].innerText.replace("$", "").replace("\xa0", ""))

        name = line_attrib["name"]
        distance = line_attrib["distance"]

        demand = {
            "eco": line_attrib["paxAttEco"],
            "biz": line_attrib["paxAttBus"],
            "pre": line_attrib["paxAttFirst"]
        }

        lines.append(Line(name, distance, tax, hubs[0], demand, ticket_price, False))

    return lines


def newlines_data(lines):
    newlines = []
    base_price_per_km = _base_price_function(lines)
    for filename in NEWLINES:
        parser.parseFile(NEwLINE_PATH + filename)
        airport_list_elem = parser.getElementsByClassName("airportList")[0]
        airport_list_elem = concatenate([airport_list_elem.getElementsByClassName("greenOutline"),
                                         airport_list_elem.getElementsByClassName("yellowOutline")])
        for airport in airport_list_elem:
            content = airport.getElementsByClassName("hubCategoryBox")[0]
            demand_elem = airport.getElementsByClassName("demand")[0].getChildren()

            name = airport.getElementsByClassName("hubNameBox")[0].innerText.split()[0]
            distance = float(
                content.getElementsByClassName("lineDistance")[0].innerText.replace("km", "").replace(" ", ""))
            tax = float(content.getChildren()[3].getChildren()[0].innerHTML.replace("&nbsp;", "").replace("$/vol", ""))

            demand = {
                "eco": float(demand_elem[1].getChildren()[1].innerHTML.split()[-1]),
                "biz": float(demand_elem[2].getChildren()[1].innerHTML.split()[-1]),
                "pre": float(demand_elem[3].getChildren()[1].innerHTML.split()[-1])
            }

            ticket_price = {}
            for m in market:
                ticket_price[m] = distance * base_price_per_km[m](distance)

            newlines.append(Line(name, distance, tax, hubs[0], demand, ticket_price, True))

    return newlines


def planes_data():
    filenames = [PLANES_PATH + "short_range.html", PLANES_PATH + "middle_range.html", PLANES_PATH + "long_range.html"]
    planes = []
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

            release_year = int(list_elem.getChildren()[0].getChildren()[0].innerText)
            max_range = float(list_elem.getChildren()[1].getChildren()[0].innerText.replace("km", "").replace(" ", ""))
            cons = float(list_elem.getChildren()[2].getChildren()[0].innerText.replace("L/100km/pax", ""))
            wear_rate = float(list_elem.getChildren()[3].getChildren()[0].innerText.replace("%/100h", "")) / 100.

            planes.append(Plane(name, {"eco": pax, "biz": 0, "pre": 0}, speed, cons, max_range, price, wear_rate))

    return planes

planes_data()
lines = lines_data()
newlines = newlines_data(lines)
