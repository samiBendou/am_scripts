import csv
import json
from enum import Enum
from datetime import datetime
from datetime import timedelta

import matplotlib.pyplot as plt
from numpy import concatenate


def get_enum_value():
    return lambda e: [list(map(lambda x: x.value, l)) for l in e]


enum_value = get_enum_value()
days_per_week = 7


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

    def __init__(self, filename=None):
        self.filename = filename
        self.date = None
        self.covered = 0
        self.fields = {}
        if filename is not None:
            self.read()

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
        self.date = data.date
        self.covered = data.covered

    """
    @brief Updates main financial data json file with self data
    @details self data is merged with main json file and is renamed to main.json
    """

    def update(self):
        filename = self.filename
        self.merge(Data("main.json"))
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
        delta = self.date - data.date

        assert data.covered >= self.covered

        if abs(delta.days) > 8:
            raise NotImplementedError

        if delta > timedelta(0):
            add_day = 1 if ((delta - timedelta(days=delta.days)) + data.date).day != data.date.day else 0
            shift_day = self.covered - add_day - delta.days - 1
            all_keys = Data.all_keys()

            for key in all_keys:
                if key == Key.__date__:
                    continue
                try:
                    new_sub = list(self.fields[key][Field.data.value][shift_day:])
                except KeyError:
                    new_sub = [0] * (add_day + delta.days + 1)
                    if data.fields[key] is None:
                        continue
                    self.fields[key] = {Field.name.value: data.fields[key][Field.name.value]}
                try:
                    old_sub = list(data.fields[key][Field.data.value][:-1])
                except KeyError:
                    old_sub = [0] * (data.covered - 1)

                self.fields[key][Field.data.value] = list(concatenate([old_sub, new_sub]))

            self.covered = data.covered + add_day + delta.days

        elif delta <= timedelta(0):
            self.copy(data)

    """
    @brief Return dictionary of raw financial data sorted by Key enumeration
    @details Values are given in dollars $
    """

    def raw(self):
        y = {}
        fields = self.fields
        data_keys = Data.keys()

        for k in range(0, len(data_keys)):
            for key in data_keys[k]:
                y[key] = list(map(lambda t: abs(t), fields[key][Field.data.value]))

        return y

    """
    @brief Return dictionary of relative financial data sorted by Key enumeration
    @details Values are given in percent %
    """

    def rel(self):
        y = {}
        fields = self.fields
        data_keys = Data.keys()

        for k in range(0, len(data_keys)):
            for key in data_keys[k]:
                if key == Key.__date__:
                    continue

                y[key] = list(map(lambda x: abs(x), fields[key][Field.data.value]))
                for t in range(0, self.covered):
                    revenue = float(fields[Key.flight.value][Field.data.value][t])
                    if revenue == 0.:
                        y[key][t] = 0.
                        continue
                    y[key][t] /= revenue

        return y

    """
    @brief Return the cash flow of the airline
    @details Values are given in dollars $. The planes purchase and loan principal amount are not taken in account.
    """

    def flow(self):
        y = [0] * self.covered
        y_gain = [0] * self.covered
        y_loss = [0] * self.covered
        excluded_keys = enum_value([[Key.plane,
                                     Key.lap,
                                     Key.cka,
                                     Key.line,
                                     Key.debit,
                                     Key.credit,
                                     Key.lpa]])[0]

        for t in range(0, self.covered):
            y[t] = sum(self.fields[Key.lap.value][Field.data.value]) / days_per_week
            y_loss[t] = y[t]
            for key, field in self.fields.items():
                if key == Key.__date__ or key in excluded_keys:
                    continue
                field_data = float((field[Field.data.value][t]))
                y[t] += field_data
                if field_data > 0:
                    y_gain[t] += field_data
                else:
                    y_loss[t] -= field_data

        return y, y_gain, y_loss

    @classmethod
    def keys(cls):
        return enum_value([
            [Key.flight, Key.cka, Key.rch, Key.lap],
            [Key.sfh, Key.sft, Key.sfs],
            [Key.mia, Key.mea, Key.mss, Key.msp],
            [Key.debit, Key.credit]
        ])

    @classmethod
    def all_keys(cls):
        return [x.value for x in Key]

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
        if self.date is None or self.date < export_date:
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
            self.date = export_date
            self.covered = len(self.fields[Key.flight.value][Field.data.value])

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
            self.date = datetime.fromisoformat(self.fields[Key.__date__])
            self.covered = len(self.fields[Key.flight.value][Field.data.value])


class Plot:

    @staticmethod
    def date_ticks(data):
        x = []
        n = data.covered
        day = timedelta(days=1)

        for k in range(0, n):
            x.append((data.date - (n - 1 - k) * day).strftime("%m-%d"))
        return x

    @staticmethod
    def scale(y, div=1.e6):
        if type(y) == dict:
            new_y = dict(y)
            for key in new_y.keys():
                new_y[key] = list(map(lambda t: t / div, new_y[key]))
            return new_y
        elif type(y) == list:
            return list(map(lambda t: t / div, y))

    @staticmethod
    def flow(data):
        x = Plot.date_ticks(data)
        (y, y_gain, y_loss) = data.flow()

        y = Plot.scale(y)
        y_gain = Plot.scale(y_gain)
        y_loss = Plot.scale(y_loss)

        plt.plot(x, y, label="Cash flow")
        plt.plot(x, y_gain, label="Benefits")
        plt.plot(x, y_loss, label="Costs")
        plt.plot(x, [sum(y) / len(x)] * len(x), "--", label="Average cash flow")
        plt.plot(x, [sum(y_gain) / len(x)] * len(x), "--", label="Average benefits")
        plt.plot(x, [sum(y_loss) / len(x)] * len(x), "--", label="Average costs")
        plt.legend()
        plt.xlabel("Date MM-DD")
        plt.ylabel("Millions $")
        plt.show()

    @staticmethod
    def raw(data):
        x = Plot.date_ticks(data)
        Plot.keys(data, x, Plot.scale(data.raw()), "Date MM-DD", "Millions $")

    @staticmethod
    def relative(data):
        x = Plot.date_ticks(data)
        Plot.keys(data, x, Plot.scale(data.rel(), 1.e-2), "Date MM-DD", "Percent %")

    @staticmethod
    def keys(data, x, y, xl, yl):
        data_keys = Data.keys()

        for k in range(0, len(data_keys)):
            for key in data_keys[k]:
                plt.plot(x, y[key], label=data.fields[key][Field.name.value])
                plt.legend()
                plt.xlabel(xl)
                plt.ylabel(yl)

            plt.show()


export = Data("export.csv")
export.update()

Plot.raw(export)
Plot.relative(export)
Plot.flow(export)
