# CS262 WhatApp dup

## Overview
This project is a distributed chat application implementing both JSON and wire protocol communication methods.

## Configuration
Configuration is managed through a `.env` file, which dynamically updates both the server and client configurations.

## Server Setup
### Running the Server
```
python server.py
```

### Protocol Selection
To switch between JSON and wire protocol:
- Uncomment/comment lines 642 and 644 in `server.py`
  - Uncomment `service_connection_json` for JSON protocol
  - Uncomment `service_connection_wp` for wire protocol

## Client Setup
### Running the Client
```
python app.py
```

### Protocol Configuration
Modify `self.is_json` in the `App` class:
- `True` for JSON protocol
- `False` for wire protocol

## Experiments
### Running Latency Tests
```
python experiment.py
```

**Note**: Manually update the protocol in the `experiment.py` file before running.

## Unit Testing
### Running Unit Tests
```
python -m unittest server_unit_tests.py
```

### SETUP
- Ensure the server is running on the specified host/port (default: `127.0.0.1:54400`)

## Environment Setup
1. Create a `.env` file with the following variables:
   ```
   HOST_SERVER=IP_FOR_SERVER_DEVICE
   PORT_SERVER=PORT_NUMBER
   SERVER_IP=0.0.0.0 or ""
   ```

## Dependencies
- Python 3.x
- socket
- threading
- json
- python-dotenv
