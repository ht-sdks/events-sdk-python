PWD := $(shell pwd)
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

build:
	docker build -t events-sdk-python/${BRANCH} .

clean:
	docker rmi events-sdk-python/${BRANCH}

format:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	ruff check --fix hightouch/htevents/
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	ruff format hightouch/htevents/

test:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	python -m unittest hightouch.htevents.test.all

repl:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} python

shell:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	sh

.PHONY: build clean repl format test shell
