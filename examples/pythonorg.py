from industrialise import browser

b = browser.Browser()
b.go("http://python.org/")
b.follow("Download")
texts = b.find('//div[@id="download-python"]/p/a[@class="reference external"]/text()')

print "Latest Python versions:"
for text in texts[:2]:
    print text
