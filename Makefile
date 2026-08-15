.PHONY: all check render clean

all: check render

check:
	xmllint --noout --schema psalter.xsd psalter.xml

render: check
	python3 renderToHTML.py psalter.xml > psalter.html

clean:
	rm -f psalter.html
