import csv
import json
from datetime import datetime
from datetime import timedelta

import matplotlib.pyplot as plt
from numpy import concatenate

day = timedelta(days=1)

days_per_week = 7

EXPORTS_ROOT = "exports/"

plot_when_get = True

subplot_keys = [
    ["flight", "aircraft.checkA", "airline.research", "finance.loanAutomaticPayment"],
    ["staff.iata.hire", "staff.iata.training", "staff.salary"],
    ["marketing.internalAudit", "marketing.externalAudit", "marketing.superSimulation",
     "marketing.simulationPurchase"],
    ["finances.debitSum", "finances.creditSum"]
]

excluded_keys = [
    "aircraft.purchase",
    "finance.loanAutomaticPayment",
    "aircraft.checkA",
    "network.linePurchase",
    "finances.debitSum",
    "finances.creditSum"
]


class FinancialData:
    def __init__(self, filename="export.csv"):
        self.filename = EXPORTS_ROOT + filename
        self.date = datetime.now()
        self.fields = {"date": self.date.isoformat()}

    def read_csv(self):
        with open(self.filename, "r") as csv_export:
            exports_reader = csv.reader(csv_export, delimiter=';')
            exports_matrix = []
            for row in exports_reader:
                exports_matrix.append(row)

        # Reading date
        datetime_split = exports_matrix[0][0].replace("#", "").split(" ")
        date_split = datetime_split[0].split("-")
        time_split = datetime_split[1].split(":")
        export_date = datetime(year=int(date_split[0]), month=int(date_split[1]), day=int(date_split[2]),
                               hour=int(time_split[0]), minute=int(time_split[1]), second=int(time_split[2]))

        fields = {"date": export_date.isoformat()}

        exports_matrix.remove(exports_matrix[1])
        exports_matrix.remove(exports_matrix[0])

        for row in exports_matrix:
            fields[row[0]] = {
                "verbose": str(row[1]).replace("\u00e9", "e").replace("\u00f4", "o").replace("\u00ea", "e"),
                "data": []
            }
            for value in row:
                try:
                    fields[row[0]]["data"].append(float(value))
                except ValueError:
                    continue

        self.fields = fields
        self.date = export_date

    def str_json(self):
        return json.dumps(self.fields, indent=4)

    def write_json(self):
        json_split = self.filename.split("/")
        json_filename = json_split[-1].replace(".csv", ".json")

        json_data = FinancialData(filename=self.filename)
        try:
            json_data.read_json()
            delta = abs(self.date - json_data.date)
            if json_data.date < self.date:
                for key, field in json_data.fields.items():
                    try:
                        len_field = len(self.fields[key]["data"])
                        sub_field = list(self.fields[key]["data"][(len_field - delta.days - 2): len_field])
                        json_sub_field = list(field["data"][:(len(field["data"]) - delta.days - 2)])
                        self.fields[key]["data"] = list(concatenate([json_sub_field, sub_field]))
                    except TypeError:
                        json_data.date = self.date
                        continue
            else:
                self.fields = json_data.fields
                self.date = json_data.date
                with open(EXPORTS_ROOT + json_filename, "w") as json_file:
                    json.dump(self.fields, json_file, indent=4)

        except FileNotFoundError:
            with open(EXPORTS_ROOT + json_filename, "w") as json_file:
                json.dump(self.fields, json_file, indent=4)

    def read_json(self):
        json_split = self.filename.split("/")
        json_filename = json_split[-1].replace(".csv", ".json")
        with open(EXPORTS_ROOT + json_filename, "r") as json_file:
            self.fields = json.load(json_file)
            self.date = datetime.fromisoformat(self.fields["date"])

    def get_formated_date_x(self):
        x = []
        n = len(self.fields["flight"]["data"])
        for k in range(0, n):
            x.append((self.date - (n - 1 - k) * day).strftime("%m-%d"))
        return x

    def get_raw_data(self):
        x = self.get_formated_date_x()
        y = {}
        fields = self.fields

        for k in range(0, len(subplot_keys)):
            for key in subplot_keys[k]:
                y[key] = list(map(lambda t: abs(t) / 1.e6, fields[key]["data"]))
                if not plot_when_get:
                    continue
                plt.plot(x, y[key], label=fields[key]["verbose"])

            if not plot_when_get:
                continue
            plt.legend()
            plt.xlabel("Date MM-DD")
            plt.ylabel("Millions $")
            plt.show()

        return y

    def get_rel_data(self):
        x = self.get_formated_date_x()
        y = {}
        fields = self.fields

        for k in range(0, len(subplot_keys)):
            for key in subplot_keys[k]:
                y[key] = []
                for t in range(0, len(x)):
                    flights_revenue = float(fields["flight"]["data"][t])
                    try:
                        y[key].append((100 * abs(fields[key]["data"][t]) / flights_revenue) if flights_revenue > 0. else 0)
                    except TypeError:
                        continue
                    except ZeroDivisionError:
                        y[key].append(0)

                if not plot_when_get:
                    continue

                plt.plot(x, y[key], label=fields[key]["verbose"])
                plt.legend()
                plt.xlabel("Date MM-DD")
                plt.ylabel("Percent %")

            if not plot_when_get:
                continue
            plt.show()

        return y

    def get_cashflow(self):
        x = self.get_formated_date_x()
        y = []
        y_gain = []
        y_loss = []

        for t in range(0, len(x)):
            y.append(sum(self.fields["finance.loanAutomaticPayment"]["data"]) / days_per_week / 1.e6)
            y_gain.append(0)
            y_loss.append(y[t])
            for key, field in self.fields.items():

                try:
                    if key in excluded_keys:
                        continue
                    else:
                        field_data = float((field["data"][t])) / 1.e6
                        y[t] += field_data
                        if field_data > 0:
                            y_gain[t] += field_data
                        else:
                            y_loss[t] -= field_data

                except TypeError:
                    continue

        if not plot_when_get:
            return y

        plt.plot(x, y, label="Cashflow")
        plt.plot(x, y_gain, label="Gain")
        plt.plot(x, y_loss, label="Loss")
        plt.plot(x, [sum(y) / len(x)] * len(x), '--', label="Average cashflow")
        plt.plot(x, [sum(y_gain) / len(x)] * len(x), '--', label="Average gain")
        plt.plot(x, [sum(y_loss) / len(x)] * len(x), '--', label="Average loss")
        plt.legend()
        plt.xlabel("Date MM-DD")
        plt.ylabel("Millions $")
        plt.show()

        return y


export_data = FinancialData("export_new.csv")
export_data.read_csv()
export_data.write_json()
print(export_data.str_json())

export_data.get_cashflow()
export_data.get_rel_data()
export_data.get_raw_data()
