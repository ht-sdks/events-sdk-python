BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
build:
	docker build -t events-sdk-python/${BRANCH} .

BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
clean:
	docker rmi events-sdk-python/${BRANCH}

BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
repl:
	docker run --rm -it events-sdk-python/${BRANCH} python

BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
pylint:
	docker run --rm -it events-sdk-python/${BRANCH} \
	pylint --rcfile=.pylintrc --reports=y --exit-zero segment/analytics | tee pylint.out

BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
flake8:
	docker run --rm -it events-sdk-python/${BRANCH} \
	flake8 --max-complexity=10 --statistics segment/analytics > flake8.out || true

BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
test:
	docker run --rm -it events-sdk-python/${BRANCH} \
	python -m unittest segment.analytics.test.all

release:
	python setup.py sdist bdist_wheel
	twine upload dist/*

e2e_test:
	.buildscripts/e2e.sh

.PHONY: build clean repl pylint flake8 test release e2e_test
