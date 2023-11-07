# Events SDK Python

## Installation

Install `hightouch-analytics-python` using pip:

```bash
pip3 install hightouch-analytics-python
```

or you can clone this repo:

```bash
git clone https://github.com/ht-sdks/events-sdk-python.git

cd events-sdk-python

sudo python3 setup.py install
```

## Usage

By default, you do not need to manually instantiate the client. Simply set your key and start calling methods.

```python
import hightouch.analytics as analytics

analytics.write_key = 'YOUR_WRITE_KEY'

analytics.identify('foo', {
    'email': 'bat@example.com',
    'name': 'Person People',
})

analytics.track('foo')
```

**Note** If you need to send data to multiple Hightouch sources, you can initialize one new Client per `write_key`. Only instantiate one `Client` class per write key per application.

```python
import hightouch.analytics as analytics
from hightouch.analytics.client import Client

analytics.write_key = 'YOUR_WRITE_KEY'
other_analytics = Client('<OTHER_WRITE_KEY>')

analytics.identify('foo', {
    'email': 'bat@example.com',
    'name': 'Person People',
})

other_analytics.identify('foo', {
    'email': 'bat@example.com',
    'name': 'Person People',
})
```
