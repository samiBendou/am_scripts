import csv
import json
from datetime import datetime
from datetime import timedelta
from enum import Enum
from DateBase import DateBase
from matplotlib.colors import rgb2hex
import matplotlib.pyplot as plt
import numpy as np


def get_enum_value():
    return lambda e: [list(map(lambda x: x.value, l)) for l in e]


enum_value = get_enum_value()


# Represents the fields name in csv export from AM2+
class Key(Enum):
    __date__ = "date"

    flight = "flight"
    plane = "aircraft.purchase"
    line = "network.linePurchase"
    rch = "airline.research"
    tax = "airline.incomeTax"
    success = "achievement.success"
    ict = "incident"
    misc = "divers"

    cka = "aircraft.checkA"
    ckd = "aircraft.checkD"

    lap = "finance.loanAutomaticPayment"
    lpa = "finance.loanPrincipalAmount"

    sfh = "staff.iata.hire"
    sft = "staff.iata.training"
    sfs = "staff.salary"

    mia = "marketing.internalAudit"
    mea = "marketing.externalAudit"
    mss = "marketing.superSimulation"
    msp = "marketing.simulationPurchase"

    debit = "finances.debitSum"
    credit = "finances.creditSum"


class Field(Enum):
    name = "verbose"
    data = "data"


class Data:
    EXPORTS_ROOT = "exports/"

    keys = enum_value([
        [Key.flight, Key.cka, Key.rch, Key.lap],
        [Key.flight, Key.sfh, Key.sft, Key.sfs],
        [Key.flight, Key.mia, Key.mea, Key.mss, Key.msp],
        [Key.flight, Key.debit, Key.credit]
    ])

    all_keys = [x.value for x in Key]

    def __init__(self, filename=None, period=None, offset=None, start=None, end=None):
        self.filename = filename
        self.base = DateBase()
        self.fields = {}
        if filename is not None:
            self.read()
            self.base.set(period, offset, start, end)

    def __str__(self):
        return json.dumps(self.fields, indent=4)

    """
    @brief switches files format contained in filename
    """

    def switch(self):
        if self.filename.split(".")[1] == "csv":
            self.filename = self.filename.replace(".csv", ".json")
        else:
            self.filename = self.filename.replace(".json", ".csv")

    """
    @brief Reads file located at exports/filename where filename is the current filename of the object
    @details When reading a file, current object state is reset
    """

    def read(self):
        ext = self.filename.split(".")[1]
        if ext == "json":
            self._read_json()
        elif ext == "csv":
            self._read_csv()
        else:
            print("File format .{} not handled for reading", ext)
            raise NotImplementedError

        self.base.set()

    """
    @brief Writes file located at exports/filename where filename is the current filename of the object
    @details If the file already exists than existing data and self data are merged (see merge function).
    """

    def write(self):
        ext = self.filename.split(".")[1]
        if ext == "json":
            self._write_json()
        else:
            print("File format .{} not handled for writing", ext)
            raise NotImplementedError

    def copy(self, data):
        self.fields = data.fields
        self.base = DateBase(covered=data.base.covered, date=data.base.date)

    """
    @brief Updates main financial data json file with self data
    @details self data is merged with main json file and is renamed to main.json
    """

    def update(self):
        filename = self.filename
        self.filename = "main.json"
        self.write()
        self.filename = filename

    """
    @param data object representing financial data updated from main report
    @brief Merge two Data objects in self object
    @details Self data are updated during merge process. If self data are older than data to merge, the data to merge
    are copied into self data. Else self data are augmented by concatenating older data and newer data
    """

    def merge(self, data):
        delta = self.base.date - data.base.date

        assert data.base.covered >= self.base.covered

        if abs(delta.days) > 8:
            raise NotImplementedError

        if delta > timedelta(0):
            add_day = 1 if ((delta - timedelta(days=delta.days)) + data.base.date).day != data.base.date.day else 0
            shift_day = self.base.covered - add_day - delta.days - 1
            for key in Data.all_keys:
                if key == Key.__date__:
                    continue
                try:
                    new_sub = list(self.fields[key][Field.data.value][shift_day:])
                except KeyError:
                    new_sub = [0] * (add_day + delta.days + 1)
                    try:
                        self.fields[key] = {Field.name.value: data.fields[key][Field.name.value]}
                    except KeyError:
                        continue
                try:
                    old_sub = list(data.fields[key][Field.data.value][:-1])
                except KeyError:
                    old_sub = [0] * (data.base.covered - 1)
                self.fields[key][Field.data.value] = list(np.concatenate([old_sub, new_sub]))

            self.base.reset(covered=data.base.covered + add_day + delta.days)

        else:
            self.copy(data)

    """
    @brief Return dictionary of raw financial data sorted by Key enumeration
    @details Values are given in dollars $
    """

    def raw(self):
        y = {}
        for k in range(0, len(Data.keys)):
            for key in Data.keys[k]:
                y[key] = list(map(lambda t: abs(t), self.fields[key][Field.data.value]))

        return self.reduce(y)

    """
    @brief Return dictionary of relative financial data sorted by Key enumeration
    @details Values are given in percent %
    """

    def rel(self):
        data = self.raw()
        y = {}
        for k in range(0, len(Data.keys)):
            for key in Data.keys[k]:
                if key == Key.__date__:
                    continue
                y[key] = data[key].copy()
                for t in range(0, self.base.range):
                    revenue = float(data[Key.flight.value][t])
                    if revenue == 0.:
                        y[key][t] = 0 if key != Key.flight.value else 1
                        continue
                    y[key][t] /= revenue

        return y

    """
    @brief Return the cash flow of the airline
    @details Values are given in dollars $. The planes purchase and loan principal amount are not taken in account.
    """

    def flow(self):
        excluded_keys = enum_value([[Key.plane,
                                     Key.lap,
                                     Key.cka,
                                     Key.line,
                                     Key.debit,
                                     Key.credit,
                                     Key.lpa]])[0]

        y = {"flow": [0] * self.base.covered, "gain": [0] * self.base.covered, "loss": [0] * self.base.covered}
        for t in range(0, self.base.covered):
            y["flow"][t] = sum(self.fields[Key.lap.value][Field.data.value]) / 7.
            y["loss"][t] = y["flow"][t]
            for key, field in self.fields.items():
                if key == Key.__date__ or key in excluded_keys:
                    continue
                field_data = float((field[Field.data.value][t]))
                y["flow"][t] += field_data
                if field_data > 0:
                    y["gain"][t] += field_data
                else:
                    y["loss"][t] -= field_data

        return self.reduce(y)

    """
    @param thd Threshold to exclude data.
    @brief Returns pie represented by average of current data set
    @details Filter the values returned by raw function in order to get only
             average value of keys which are greater than the threshold.
    @return a dictionary with the remaining keys and the average value
    """

    def pie(self, thd=0.):
        excluded_keys = enum_value([[Key.debit, Key.credit]])[0]

        # Filtering keys
        raw = self.raw()
        for key, field in self.fields.items():
            if key == Key.__date__ or key in excluded_keys:
                continue
            if abs(sum(field[Field.data.value])) / self.base.range < thd * self.base.period:
                excluded_keys.append(key)

        for key in excluded_keys:
            try:
                del raw[key]
            except KeyError:
                continue

        # Averaging values
        keys = list(filter(lambda x: True if x not in excluded_keys else False, list(raw.keys())))
        values = np.array(list(raw.values())).mean(axis=1)
        return dict(zip(keys, values))

    def reduce(self, y):
        y_reduced = {}
        for key, val in y.items():
            y_reduced[key] = [0] * self.base.range
            for t in range(0, self.base.range * self.base.period):
                try:
                    shift = self.base.offset * self.base.period + self.base.start
                    y_reduced[key][int(t / self.base.period)] += y[key][t + shift]
                except IndexError:
                    continue

        return y_reduced

    def _read_csv(self):
        with open(Data.EXPORTS_ROOT + self.filename, "r") as csv_export:
            exports_reader = csv.reader(csv_export, delimiter=";")
            exports_matrix = []
            for row in exports_reader:
                exports_matrix.append(row)

        # Reading date
        datetime_split = exports_matrix[0][0].replace("#", "").split(" ")
        date_split = datetime_split[0].split("-")
        time_split = datetime_split[1].split(":")
        export_date = datetime(year=int(date_split[0]), month=int(date_split[1]), day=int(date_split[2]),
                               hour=int(time_split[0]), minute=int(time_split[1]), second=int(time_split[2]))

        # Current data are already up to date
        if self.base.date is None or self.base.date < export_date:
            fields = {Key.__date__: export_date.isoformat()}

            exports_matrix.remove(exports_matrix[1])
            exports_matrix.remove(exports_matrix[0])

            for row in exports_matrix:
                fields[row[0]] = {
                    Field.name.value: str(row[1]).replace("\u00e9", "e").replace("\u00f4", "o").replace("\u00ea", "e"),
                    Field.data.value: []
                }
                for value in row:
                    try:
                        fields[row[0]][Field.data.value].append(float(value))
                    except ValueError:
                        continue

            self.fields = fields
            self.base.reset(date=export_date,
                            covered=len(self.fields[Key.flight.value][Field.data.value]))

    def _write_json(self):
        try:
            data = Data(filename=self.filename)
            self.merge(data)
            with open(Data.EXPORTS_ROOT + self.filename, "w") as json_file:
                json.dump(self.fields, json_file, indent=4)

        except FileNotFoundError:
            with open(Data.EXPORTS_ROOT + self.filename, "w") as json_file:
                json.dump(self.fields, json_file, indent=4)

    def _read_json(self):
        json_filename = self.filename.replace(".csv", ".json")
        with open(Data.EXPORTS_ROOT + json_filename, "r") as json_file:
            self.fields = json.load(json_file)
            self.base.reset(date=datetime.fromisoformat(self.fields[Key.__date__]),
                            covered=len(self.fields[Key.flight.value][Field.data.value]))


class Plot:
    @staticmethod
    def date_ticks(data):
        ticks = list(map(lambda t: t.strftime("%m-%d"), data.base.list()))
        return ticks

    @staticmethod
    def scale(y, div=1.e6):
        new_y = y.copy()
        for key in list(new_y.keys()):
            new_y[key] = list(map(lambda t: t / div, new_y[key]))
        return new_y

    @staticmethod
    def raw(data, average=False):
        x = Plot.date_ticks(data)
        y = Plot.scale(data.raw())
        label = {key: data.fields[key][Field.name.value] for key in list(y.keys())}
        for keys in Data.keys:
            Plot.keys(x, {key: y[key] for key in keys}, "Date MM-DD", "Millions $", label, average)

    @staticmethod
    def rel(data, average=False):
        x = Plot.date_ticks(data)
        y = Plot.scale(data.rel(), 1.e-2)
        label = {key: data.fields[key][Field.name.value] for key in list(y.keys())}
        for keys in Data.keys:
            Plot.keys(x, {key: y[key] for key in keys}, "Date MM-DD", "Percent %", label, average)

    @staticmethod
    def flow(data, average=False):
        x = Plot.date_ticks(data)
        y = Plot.scale(data.flow())
        label = {"flow": "Cash flow", "gain": "Benefits", "loss": "Costs"}
        Plot.keys(x, y, "Date MM-DD", "Millions $", label, average)

    @staticmethod
    def pie(data):
        y = data.pie(thd=3.e5)
        size = 0.3
        fig, ax = plt.subplots()
        colors = plt.get_cmap("Set3")(np.arange(len(y)))
        title = "Budget repartition : "
        title += data.base.bound("start").strftime("%m-%d-%y") + " -> " + data.base.bound("end").strftime("%m-%d-%y")
        ax.pie(list(y.values()),
               radius=1,
               wedgeprops=dict(width=size, edgecolor="w"),
               colors=colors,
               labels=[data.fields[key][Field.name.value] for key in list(y.keys())],
               autopct="%1.1f%%"
               )
        ax.set(aspect="equal", title=title)
        plt.show()

    @staticmethod
    def keys(x, y, xl, yl, label, average=False):
        keys = list(y.keys())
        n = len(x)
        colors = plt.get_cmap("Dark2")(np.arange(len(keys)))
        for k in range(0, len(keys)):
            plt.plot(x, y[keys[k]], label=label[keys[k]], color=rgb2hex(colors[k][:3]))
            if average is True:
                y_avg = [sum(y[keys[k]]) / len(y[keys[k]])] * n
                plt.plot(x, y_avg, "--", label=None, color=rgb2hex(colors[k][:3]))
            plt.legend()
            plt.xlabel(xl)
            plt.ylabel(yl)

        plt.show()
