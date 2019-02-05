import csv
import json
from enum import Enum

from Airport import Airport
from Plane import Plane

OPENFLIGHTS_ROOT = "openflights/"


class AirportKeys(Enum):
    id = 0
    name = 1
    city = 2
    country = 3
    iata = 4
    icao = 5
    lat = 6
    lon = 7
    alt = 8
    tmz = 9


class PlanesKeys(Enum):
    name = 0
    iata = 1
    icao = 2


all_keys = {"airports": {x.name: x.value for x in AirportKeys}, "planes": {x.name: x.value for x in PlanesKeys}}


def _read_csv(filename):
    with open(OPENFLIGHTS_ROOT + filename, "r") as csv_file:
        csv_reader = csv.reader(csv_file)
        csv_matrix = []
        for row in csv_reader:
            csv_matrix.append(row)

    return csv_matrix


def _read_airports(as_dict=False):
    csv_matrix = _read_csv("airports.csv")
    airports_dict = {}
    for row in csv_matrix:
        airports_dict[row[AirportKeys.iata.value]] = {x.name: row[x.value] for x in AirportKeys}

    return airports_dict if as_dict else {key: _parse_airport(airport) for key, airport in airports_dict.items()}


def _read_planes(as_dict=False):
    csv_matrix = _read_csv("planes.csv")
    planes_dict = {}
    for row in csv_matrix:
        planes_dict[row[PlanesKeys.iata.value]] = {x.name: row[x.value] for x in PlanesKeys}

    return planes_dict if as_dict else {key: _parse_plane(plane) for key, plane in planes_dict.items()}


def _parse_plane(plane):
    return Plane(plane[PlanesKeys.name.name], 0., 0., 0., 0., 0.)


def _parse_airport(airport):
    lat = float(airport[AirportKeys.lat.name])
    lon = float(airport[AirportKeys.lon.name])
    iata = airport[AirportKeys.iata.name]
    name = airport[AirportKeys.name.name]
    country = airport[AirportKeys.country.name]
    city = airport[AirportKeys.city.name]
    try:
        tmz = float(airport[AirportKeys.tmz.name])
    except ValueError:
        tmz = 0

    return Airport(lat, lon, 0., 0., iata, name, {"country": country, "city": city, "tmz": tmz})


airports = _read_airports()
planes = _read_planes()
