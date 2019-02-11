import scrap

scrap.HTML.read()

scrap.JSON.planes = scrap.HTML.planes
scrap.JSON.lines = scrap.HTML.lines
scrap.JSON.airports = scrap.HTML.airports

scrap.JSON.write()
