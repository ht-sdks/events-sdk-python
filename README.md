# Events SDK Python

## Installation

Install `events-sdk-python` using pip:

```bash
python -m pip install events-sdk-python
```

## Usage

By default, you do not need to manually instantiate the client. Simply set your key and start calling methods.

```python
import hightouch.htevents as htevents

htevents.write_key = 'YOUR_WRITE_KEY'

htevents.identify('userId1', {
    'email': 'bat@example.com',
    'name': 'Person People',
})

htevents.track('userId1', 'Order Completed', {})
```

**Note** If you need to send data to multiple Hightouch sources, you can initialize one new Client per `write_key`.

```python
from hightouch.htevents.client import Client

htevents.write_key = 'YOUR_WRITE_KEY'
other_htevents = Client('<OTHER_WRITE_KEY>')

htevents.identify('userId1', {
    'email': 'bat@example.com',
    'name': 'Person People',
})

other_htevents.identify('userId1', {
    'email': 'bat@example.com',
    'name': 'Person People',
})

htevents.track('userId1', 'Order Completed', {})
other_htevents.track('userId1', 'Order Completed', {})
```

**Note** Only instantiate `Client` class **once** per write key, per application.

```python
from flask import Flask
from hightouch.htevents.client import Client

app = Flask(__name__)

// For example, in flask, instantiate the client outside of the request handlers
htevents = Client('<WRITE_KEY>')

@app.route('/')
def hello_world():
   htevents.track('userId1', 'hello', {})
   return 'Hello World'
```
