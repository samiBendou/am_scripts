import csv
import json
from enum import Enum
from datetime import datetime
from datetime import timedelta

import matplotlib.pyplot as plt
from numpy import concatenate

day = timedelta(days=1)

days_per_week = 7

EXPORTS_ROOT = "exports/"

plot_when_get = True


# Represents the fields name in csv export from AM2-pro

class Key(Enum):
    __date__ = "date"

    period = "period"
    flight = "flight"
    rch = "airline.research"
    plane = "aircraft.purchase"
    loan = "finance.loanAutomaticPayment"
    check = "aircraft.checkA"
    line = "network.linePurchase"
    tax = "airline.incomeTax"
    ict = "incident"
    success = "achievement.success"

    sfh = "staff.iata.hire"
    sft = "staff.iata.training"
    sfs = "staff.salary"

    mia = "marketing.internalAudit"
    mea = "marketing.externalAudit"
    mss = "marketing.superSimulation"
    msp = "marketing.simulationPurchase"

    misc = "divers"

    debit = "finances.debitSum"
    credit = "finances.creditSum"


class Field(Enum):
    name = "verbose"
    data = "data"


def get_enum_value():
    return lambda e: [list(map(lambda x: x.value, l)) for l in e]


enum_value = get_enum_value()

get_data_keys = enum_value([
    [Key.flight, Key.check, Key.rch, Key.loan],
    [Key.sfh, Key.sft, Key.sfs],
    [Key.mia, Key.mea, Key.mss, Key.msp],
    [Key.debit, Key.credit]
])


class Data:
    def __init__(self, filename=None):
        self.filename = filename
        self.date = None
        self.covered = 0
        self.fields = {}
        if filename is not None:
            self.read()

    def __str__(self):
        return json.dumps(self.fields, indent=4)

    def read(self):
        ext = self.filename.split(".")[1]
        if ext == "json":
            self._read_json()
        elif ext == "csv":
            self._read_csv()
        else:
            print("File format .{} not handled for reading", ext)
            raise NotImplementedError

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
        @param data object representing financial data updated from main report
        @brief Merge two Data objects in self object
        @details Self data are updated during merge process. If self data are older than data to merge, than self data
        are erased
    """
    def merge(self, data):
        delta = self.date - data.date

        assert data.covered >= self.covered

        if abs(delta.days) > 8:
            raise NotImplementedError

        if delta > timedelta(0):
            shift_day = 1 if ((delta - timedelta(days=delta.days)) + data.date).day != data.date.day else 0
            self.covered = data.covered + shift_day + delta.days
            for key, field in self.fields.items():
                if key == Key.__date__:
                    continue
                try:
                    new_sub = list(field[Field.data.value][(self.covered - shift_day - delta.days - 1):])
                    old_sub = list(data.fields[key][Field.data.value][:-1])
                    field[Field.data.value] = list(concatenate([old_sub, new_sub]))

                except KeyError:
                    continue

            self.covered = len(self.fields[Key.flight.value][Field.data.value])

        elif delta <= timedelta(0):
            self.copy(data)

    def raw(self):
        y = {}
        fields = self.fields

        for k in range(0, len(get_data_keys)):
            for key in get_data_keys[k]:
                y[key] = list(map(lambda t: abs(t), fields[key][Field.data.value]))

        return y

    def rel(self):
        y = {}
        fields = self.fields

        for k in range(0, len(get_data_keys)):
            for key in get_data_keys[k]:
                if key == Key.__date__:
                    continue

                y[key] = [0.] * self.covered
                for t in range(0, self.covered):
                    flights_revenue = float(fields[Key.flight.value][Field.data.value][t])
                    try:
                        y[key][t] = abs(fields[key][Field.data.value][t]) / flights_revenue
                    except ZeroDivisionError:
                        continue

        return y

    def flow(self):
        y = []
        y_gain = []
        y_loss = []
        excluded_keys = enum_value([[Key.plane, Key.loan, Key.check, Key.line, Key.debit, Key.credit]])[0]

        for t in range(0, self.covered):
            y.append(sum(self.fields[Key.loan.value][Field.data.value]) / days_per_week)
            y_gain.append(0)
            y_loss.append(y[t])
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

    def _read_csv(self):
        with open(EXPORTS_ROOT + self.filename, "r") as csv_export:
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

        data = Data(filename=self.filename)
        try:
            data._read_json()
            self.merge(data)
            with open(EXPORTS_ROOT + self.filename, "w") as json_file:
                json.dump(self.fields, json_file, indent=4)

        except FileNotFoundError:
            with open(EXPORTS_ROOT + self.filename, "w") as json_file:
                json.dump(self.fields, json_file, indent=4)

    def _read_json(self):
        json_filename = self.filename.replace(".csv", ".json")
        with open(EXPORTS_ROOT + json_filename, "r") as json_file:
            self.fields = json.load(json_file)
            self.date = datetime.fromisoformat(self.fields[Key.__date__])
            self.covered = len(self.fields[Key.flight.value][Field.data.value])


class Plot:

    @staticmethod
    def date_ticks(data):
        x = []
        n = data.covered
        for k in range(0, n):
            x.append((data.date - (n - 1 - k) * day).strftime("%m-%d"))
        return x

    @staticmethod
    def cash_flow(data):
        x = Plot.date_ticks(data)
        (y, y_gain, y_loss) = data.flow()

        plt.plot(x, y, label="Cashflow")
        plt.plot(x, y_gain, label="Gain")
        plt.plot(x, y_loss, label="Loss")
        plt.plot(x, [sum(y) / len(x)] * len(x), "--", label="Average cashflow")
        plt.plot(x, [sum(y_gain) / len(x)] * len(x), "--", label="Average gain")
        plt.plot(x, [sum(y_loss) / len(x)] * len(x), "--", label="Average loss")
        plt.legend()
        plt.xlabel("Date MM-DD")
        plt.ylabel("Millions $")
        plt.show()

    @staticmethod
    def raw(data):
        x = Plot.date_ticks(data)
        y = data.raw()
        Plot.keys(data, x, y, "Date MM-DD", "Millions $")

    @staticmethod
    def relative(data):
        x = Plot.date_ticks(data)
        y = data.rel()
        Plot.keys(data, x, y, "Date MM-DD", "Percent %")

    @staticmethod
    def keys(data, x, y, xl, yl):
        for k in range(0, len(get_data_keys)):
            for key in get_data_keys[k]:
                plt.plot(x, y[key], label=data.fields[key][Field.name.value])
                plt.legend()
                plt.xlabel(xl)
                plt.ylabel(yl)

            plt.show()


export = Data("export_new.csv")
export.merge(Data("export.csv"))

Plot.raw(export)
Plot.relative(export)
Plot.cash_flow(export)
