"""
Tools for accounting and financial analysis.

Finance modules offers both a data interface with CSV financial records from AM2+ and plotting features to perform
advanced accounting over your airline.

In order to provide a long term analysis (month, year) a local record of financial data must be created and
maintained each time you load new financial data. The file used for this purpose is main.json located at exports/ .
Each to you load new financial data, theses new data are merged with main.json so it contains all the financial data
from the first export you have loaded.
"""

import csv
import json
from enum import Enum
from utilities import *
from matplotlib.colors import rgb2hex
import matplotlib.pyplot as plt
import numpy as np


class Key(Enum):
    """Enumeration of lines labels in AM2+ CSV financial records. Not exhaustive."""
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
    """Enumeration of keys for each lines in AM2+ CSV financial records. Used for JSON recording"""
    name = "verbose"
    data = "data"


class Data:
    """
    Data class represents either a CSV or a JSON file containing AM2+ financial records.

    The class provides reading and writing features in JSON and can load CSV files from AM2+ and
    computation of detailed financial results.

    The data are represented in memory using a dictionary and some meta-data.
    They are always stored as daily data but indicators can be obtained as average data over any period (weekly, month,
    63 days, ...) starting and ending at any time.


    Attributes:
        filename (str): Name of the file to load. Precise relative path from exports directory in project root.
        eg. "exports.csv" will load the file located at exports/exports.csv
        base (DateBase): Date base representing the duration and periodicity of data.
        fields (dict): Dictionary of financial reports fields. Indexed by Key enumeration. Each value of this
        dictionary is a dictionary index by Field enumeration. The value at "data" key is an array representing
        daily cash flow for "verbose" key for the covered period
    """

    EXPORTS_ROOT = "exports/"

    keys = enum_value([
        [Key.flight, Key.cka, Key.rch, Key.lap],
        [Key.flight, Key.sfh, Key.sft, Key.sfs],
        [Key.flight, Key.mia, Key.mea, Key.mss, Key.msp],
        [Key.flight, Key.debit, Key.credit]
    ])

    all_keys = [x.value for x in Key]

    def __init__(self, filename=None, period=None, offset=None, start=None, end=None):
        """
        Constructs a Data object with given filename and date base.

        Starts by reading the file at filename and than
        instantiates a date base coherent with loaded data and given parameters.

        Parameters:
            filename (str): Relative path to file to read
            period (int): Periodicity of the data for indicators computing in days eg. period=7, period="week"...
            offset (int): Offset in number of period from start day.
            start (datetime): Starting date for indicators computing
            end (datetime): Ending date for indicators computing
        """
        self.filename = filename
        self.base = DateBase()
        self.fields = {}
        if filename is not None:
            self.read()
            self.base.set(period, offset, start, end)

    def __str__(self):
        return json.dumps(self.__dict__, indent=4)

    def __dict__(self):
        return self.fields

    def switch(self):
        """Toggle files format contained in filename JSON to CSV or CSV to JSON"""
        if self.filename.split(".")[1] == "csv":
            self.filename = self.filename.replace(".csv", ".json")
        else:
            self.filename = self.filename.replace(".json", ".csv")

    def read(self):
        """
        Reads file located at exports/filename where filename is the current filename of the object.

        When reading a file, current object state is reset.
        """
        ext = self.filename.split(".")[1]
        if ext == "json":
            self._read_json()
        elif ext == "csv":
            self._read_csv()
        else:
            print("File format .{} not handled for reading", ext)
            raise NotImplementedError

        self.base.set()

    def write(self):
        """
        Writes file located at exports/filename where filename is the current filename of the object.

        If the file already exists than existing data and self data are merged (see merge function).
        """
        ext = self.filename.split(".")[1]
        if ext == "json":
            self._write_json()
        else:
            print("File format .{} not handled for writing", ext)
            raise NotImplementedError

    def copy(self, data):
        self.fields = data.fields
        self.base = DateBase(covered=data.base.covered, date=data.base.date)

    def update(self):
        """
        Updates main financial data json file with self data.

        self data is merged with main json file and is renamed to main.json
        """
        filename = self.filename
        self.filename = "main.json"
        self.write()
        self.filename = filename

    def merge(self, data):
        """
        Merge two Data objects. Self data are updated during merge process.

        If self data are older than data to merge, the data to merge are copied into self data.
        Else self data are augmented by concatenating older data and newer data

        Parameters:
            data (Data): object representing financial data updated from main report
        """
        delta = self.base.date - data.base.date

        assert data.base.covered >= self.base.covered

        if abs(delta.days) > 8:
            raise NotImplementedError

        if delta > timedelta(0):
            add_day = 1 if ((delta - timedelta(days=delta.days)) + data.base.date).day != data.base.date.day else 0
            shift_day = self.base.covered - add_day - delta.days - 1

            assert shift_day >= 0

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

    def raw(self):
        """
        Indexes raw accounting data in $ reduced according to the current date base.

        Returns:
             Dictionary of raw financial data sorted by Key enumeration. Each key stores an array representing
             an expense or an income over the period described by the current date base
        """
        y = {}
        for k in range(0, len(Data.keys)):
            for key in Data.keys[k]:
                y[key] = list(map(lambda t: abs(t), self.fields[key][Field.data.value]))

        return self.reduce(y)

    def rel(self):
        """
        Indexes relative accounting data in % reduced according to the current date base.

        Returns:
             Dictionary of relative financial data sorted by Key enumeration. Each key stores an array representing
             an expense or an income over the period described by the current date base
        """
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

    def flow(self):
        """
        Computes structural profit in $, total benefits and total costs.

        The planes purchase and loan principal amount are not taken in account in structural profit.

        Returns:
            Dictionary with profits, total benefits and total costs indexed respectively as "flow", "gain" and "loss"
            over the period described by the current date base
        """
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

    def pie(self, thd=0.):
        """
        Creates pie representing expenses and incomes of current data set.

        Filters the values returned by raw function in order to get only average value of keys
        which are greater than the threshold.

        Parameter:
            thd (float) Threshold to exclude data in $/day

        Returns:
            Dictionary with averages values of remaining Keys after filter
        """
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
        """
        Reduces a data set according to a certain date base.

        Parameter:
            y (dict): A daily data obtain with one of the function above

        Returns:
            y_reduced: Dictionary of y average values over the period described by current date base
        """
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


class Plot(GenericPlot):
    """
    Plotting static interface class

    Used as interface with matplotlib for every result that can be computed with
    Data objects.
    """

    RENDER_ROOT = GenericPlot.RENDER_ROOT + "finance/"

    @staticmethod
    def date_ticks(data):
        """Returns a list of date ticks according to given data date base"""
        ticks = list(map(lambda t: t.strftime("%m-%d"), data.base.list()))
        return ticks

    @staticmethod
    def scale(y, div=1.e6):
        """Divides the data by given coefficient"""
        new_y = y.copy()
        for key in list(new_y.keys()):
            new_y[key] = list(map(lambda t: t / div, new_y[key]))
        return new_y

    @staticmethod
    def raw(data, average=False):
        """Plots raw financial results"""
        x = Plot.date_ticks(data)
        y = Plot.scale(data.raw())
        label = {key: data.fields[key][Field.name.value] for key in list(y.keys())}

        k = 0
        for keys in Data.keys:
            Plot.keys(x, {key: y[key] for key in keys}, "Date MM-DD", "Millions $", label,
                      title="Raw Accounting {:d}".format(k + 1), date=data.base.end_date(), average=average)
            k += 1

    @staticmethod
    def rel(data, average=False):
        """Plots relative financial results"""
        x = Plot.date_ticks(data)
        y = Plot.scale(data.rel(), 1.e-2)
        label = {key: data.fields[key][Field.name.value] for key in list(y.keys())}

        k = 0
        for keys in Data.keys:
            Plot.keys(x, {key: y[key] for key in keys}, "Date MM-DD", "Percent %", label,
                      title="Relative Accounting {:d}".format(k + 1), date=data.base.end_date(), average=average)
            k += 1

    @staticmethod
    def flow(data, average=False):
        """Plots structural profits, benefits and costs"""
        x = Plot.date_ticks(data)
        y = Plot.scale(data.flow())
        label = {"flow": "Cash flow", "gain": "Benefits", "loss": "Costs"}
        Plot.keys(x, y, "Date MM-DD", "Millions $", label,
                  title="Cash flow", date=data.base.end_date(), average=average)

    @staticmethod
    def pie(data):
        """Plots pie with expenses and incomes"""
        y = data.pie(thd=3.e5)
        size = 0.3
        fig, ax = plt.subplots()
        colors = plt.get_cmap("Set3")(np.arange(len(y)))
        title = "repartition from " + data.base.start_date().strftime("%m-%d-%y")
        ax.pie(list(y.values()),
               radius=1,
               wedgeprops=dict(width=size, edgecolor="w"),
               colors=colors,
               labels=[data.fields[key][Field.name.value] for key in list(y.keys())],
               autopct="%1.1f%%"
               )
        ax.set(aspect="equal")
        Plot.render(title=title, date=data.base.end_date(), legend=False)

    @staticmethod
    def keys(x, y, xl, yl, label, title=None, date=None, average=False):
        """
        Generic plotting for financial keys.

        Parameters:
            x (list): Date ticks label data
            y (dict): Dictionary of y data list indexed by keys contained in Key enumeration
            xl (str): Label of x axis
            yl (str): Label of y axis
            label (dict): Dictionary of y data labels indexed by keys contained in Key enumeration
            title (str): Title of the plot
            date (datetime): Date of the plot. Used for file naming
            average (bool): If True plots an horizontal scattered bar representing average of the values of the field
        """
        plot_keys = list(y.keys())
        n = len(x)
        colors = plt.get_cmap("Dark2")(np.arange(len(plot_keys)))
        for k in range(0, len(plot_keys)):
            plt.plot(x, y[plot_keys[k]], label=label[plot_keys[k]], color=rgb2hex(colors[k][:3]))
            if average is True:
                y_avg = [sum(y[plot_keys[k]]) / len(y[plot_keys[k]])] * n
                plt.plot(x, y_avg, "--", label=None, color=rgb2hex(colors[k][:3]))

        Plot.render(xl, yl, title, date=date, legend=True)
