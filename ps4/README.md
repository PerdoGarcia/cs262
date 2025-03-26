# CS262 WhatApp dup

## Overview
This project is a distributed chat application implementing both JSON and wire protocol communication methods.

## Configuration
Configuration is managed through a `.env` file, which dynamically updates both the server and client configurations. Additionally our .proto contains the grpc functions in which we use to commmunicate between client and servers.

## Server Setup
For running the server, we hard code ports 5001,5002, and 5003 for simplicity.
Simply run the server and select the three distinct ports on each server


### Running the Server
```
python3 server1.py
Then you will be prompted
"Enter the port number: 5001, 5002, or 5003"
which you will enter 5001, 5002, or 5003
```

## Client Setup
### Running the Client
```
python3 app.py
```
It will automatically find the 

## Unit Testing
### Running Unit Tests
```
python unitTests.py
```

### SETUP
- Ensure the server is running on the specified host/port 

## Environment Setup
1. Create a `.env` file with the following variables:
   ```
   HOST_SERVER="10.250.88.150"
   PORT_SERVER=8080
   SERVER_IP=""
   HOST_SERVER_TESTING="0.0.0.0"
   PORT_SERVER_TESTING=5000
   GRPC_PORT = 5001
   SERVER5001="10.250.160.176"
   SERVER5002="10.250.160.176"
   SERVER5003="10.250.52.166"

   ```

## Dependencies
- Python 3.x
- socket
- threading
- json
- python-dotenv
