import finance
import purchase
import scrap

# Plot financial data
finance_data = finance.Data("export.csv")
finance_data.update()
finance.Plot.raw(finance_data)
finance.Plot.relative(finance_data)
finance.Plot.flow(finance_data)

# Plot purchase data from owned lines
planes = scrap.planes_data()
lines = scrap.lines_data()
lines.extend(scrap.newlines_data(lines))
purchase_data = purchase.Data(planes, lines)
purchase.Plot.sort(purchase_data)
