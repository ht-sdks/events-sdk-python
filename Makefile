PWD := $(shell pwd)
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

build:
	docker build -t events-sdk-python/${BRANCH} .

clean:
	docker rmi events-sdk-python/${BRANCH}

format:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	ruff check --fix hightouch/analytics/
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	ruff format hightouch/analytics/

test:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	python -m unittest hightouch.analytics.test.all

repl:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} python

shell:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	sh

.PHONY: build clean repl format test shell
