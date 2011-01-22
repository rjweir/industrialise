from collections import defaultdict

from industrialise import browser

weather = defaultdict(dict)

b = browser.Browser()
b.go("http://www.bom.gov.au/")
for t in b.find("//td[@title='Maximum temperature in degrees Celsius']/.."):
    place = t[0].text_content()
    temp = t[1].text
    forecast = t[2].text_content()
    weather[place]['max'] = temp
    weather[place]['forecast'] = forecast

for t in b.find("//td[@title='Latest temperature in degrees Celsius']/.."):
    place = t[0].text_content()
    latest = t[1].text
    weather[place]['latest'] = latest

def print_row(city, max, latest, forecast):
   print "%15s %5s %7s %s" % (city.ljust(15), max.ljust(5), latest.ljust(7), forecast)

print_row("City", "Max", "Latest", "Forecast")

for city, data in sorted(weather.iteritems()):
    print_row(city, data['max'], data['latest'], data['forecast'])
