import finance
import purchase
import scrap

# Plot financial data
export = finance.Data("export.csv")
export.update()

finance.Plot.raw(export)
finance.Plot.relative(export)
finance.Plot.flow(export)

# Plot purchase data
planes = scrap.planes_data()
lines = scrap.lines_data()
lines.extend(scrap.newlines_data(lines))
scrap = purchase.Data(planes, lines)
purchase.Plot.sort(scrap)
