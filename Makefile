forms = $(shell ls src/designer/*.ui)
compiled = $(shell echo $(forms) | sed -e 's/ui\>/py/g' -)

all: $(compiled)

%.py: %.ui
	pyuic4 '$<' -o '$@'
