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

analytics.identify('userId1', {
    'email': 'bat@example.com',
    'name': 'Person People',
})

analytics.track('userId1', 'Order Completed', {})
```

**Note** If you need to send data to multiple Hightouch sources, you can initialize one new Client per `write_key`.

```python
from hightouch.analytics.client import Client

analytics.write_key = 'YOUR_WRITE_KEY'
other_analytics = Client('<OTHER_WRITE_KEY>')

analytics.identify('userId1', {
    'email': 'bat@example.com',
    'name': 'Person People',
})

other_analytics.identify('userId1', {
    'email': 'bat@example.com',
    'name': 'Person People',
})

analytics.track('userId1', 'Order Completed', {})
other_analytics.track('userId1', 'Order Completed', {})
```

**Note** Only instantiate `Client` class **once** per write key, per application.

```python
from flask import Flask
from hightouch.analytics.client import Client

app = Flask(__name__)

// For example, in flask, instantiate the client outside of the request handlers
analytics = Client('<WRITE_KEY>')

@app.route('/')
def hello_world():
   analytics.track('userId1', 'hello', {})
   return 'Hello World'
```
