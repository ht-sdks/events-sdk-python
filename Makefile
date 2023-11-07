PWD := $(shell pwd)
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

build:
	docker build -t events-sdk-python/${BRANCH} .

clean:
	docker rmi events-sdk-python/${BRANCH}

repl:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} python

format:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	ruff check --fix hightouch/analytics/
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	ruff format hightouch/analytics/

test:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	python -m unittest hightouch.analytics.test.all

release:
	python setup.py sdist bdist_wheel
	twine upload dist/*

e2e_test:
	.buildscripts/e2e.sh

.PHONY: build clean repl format test release e2e_test
