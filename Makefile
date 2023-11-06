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
	ruff check --fix segment/analytics/
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	ruff format segment/analytics/

test:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	python -m unittest segment.analytics.test.all

release:
	python setup.py sdist bdist_wheel
	twine upload dist/*

e2e_test:
	.buildscripts/e2e.sh

.PHONY: build clean repl pylint flake8 black test release e2e_test
