import csv
import json
from datetime import datetime
from datetime import timedelta

import matplotlib.pyplot as plt
from numpy import concatenate

day = timedelta(days=1)

days_per_week = 7

EXPORTS_ROOT = "exports/"

subplot_keys = [
    ["flight", "aircraft.checkA", "incident", "divers", "finance.loanAutomaticPayment"],
    ["staff.iata.hire", "staff.iata.training", "staff.salary"],
    ["marketing.internalAudit", "marketing.externalAudit", "marketing.superSimulation",
     "marketing.simulationPurchase"],
    ["finances.debitSum", "finances.creditSum"]
]


class ExportData:
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

        json_data = ExportData(filename=self.filename)
        try:
            json_data.read_json()
            delta = abs(self.date - json_data.date)
            additional_day = 1 if self.date.day != json_data.date.day else 0
            for key, field in json_data.fields.items():
                try:
                    len_field = len(self.fields[key]["data"])
                    sub_field = list(self.fields[key]["data"][(len_field - delta.days - additional_day - 1): len_field])
                    json_sub_field = list(field["data"][:(len(field["data"]) - delta.days - additional_day)])
                    self.fields[key]["data"] = list(concatenate([json_sub_field, sub_field]))
                except TypeError:
                    continue

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
        for k in range(0, days_per_week):
            x.append((self.date - (days_per_week - 1 - k) * day).strftime("%m-%d"))
        return x

    def plot_raw_data(self):
        x = self.get_formated_date_x()
        fields = self.fields

        for k in range(0, len(subplot_keys)):
            for key in subplot_keys[k]:
                try:
                    plt.plot(x, list(map(lambda t: abs(t) / 1.e6, fields[key]["data"])), label=fields[key]["verbose"])
                except TypeError:
                    continue

            plt.legend()
            plt.xlabel("Date MM-DD")
            plt.ylabel("Millions $")
            plt.show()

    def plot_pdata(self):
        x = self.get_formated_date_x()
        fields = self.fields

        for k in range(0, len(subplot_keys)):
            for key in subplot_keys[k]:
                y = []
                for t in range(0, len(fields[key]["data"])):
                    try:
                        y.append(100 * abs(fields[key]["data"][t]) / fields["flight"]["data"][t])
                    except TypeError:
                        continue
                    except ZeroDivisionError:
                        y.append(0)

                plt.plot(x, y, label=fields[key]["verbose"])
                plt.legend()
                plt.xlabel("Date MM-DD")
                plt.ylabel("Percent %")
            plt.show()

    def plot_cashflow(self):
        x = self.get_formated_date_x()
        y = []
        excluded_keys = [
            "aircraft.purchase",
            "finance.loanAutomaticPayment",
            "aircraft.checkA",
            "network.linePurchase",
            "finances.debitSum",
            "finances.creditSum"
        ]
        for t in range(0, days_per_week):
            y.append(sum(self.fields["finance.loanAutomaticPayment"]["data"]) / days_per_week / 1.e6)
            for key, field in self.fields.items():

                try:
                    if key in excluded_keys:
                        continue
                    else:
                        y[t] += (field["data"][t]) / 1.e6
                except TypeError:
                    continue

        plt.plot(x, y, label="Cashflow")
        plt.legend()
        plt.xlabel("Date MM-DD")
        plt.ylabel("Millions $")
        plt.show()


export_data = ExportData()
export_data.read_csv()

days_per_week = 8

export_data.filename = EXPORTS_ROOT + f"export_new.csv"
export_data.read_csv()
export_data.write_json()
print(export_data.str_json())

export_data.plot_cashflow()
export_data.plot_pdata()
