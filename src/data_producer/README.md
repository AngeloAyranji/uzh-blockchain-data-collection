# Data Producer
Fetches data from nodes via RPC and puts them into a Kafka topic.

## Running the code
## Locally via Docker
```
# Build the image
$ docker build . -t data_producer
# Run it
$ docker run -it data_producer
```

### Locally via venv
Make sure your python version is at least `3.9` (`python --version`)

```
# create a virtual environment from this directory (src/data_producer)
$ python -m venv venv
# activate it
$ source ./venv/bin/activate
# install requirements
(venv) $ pip install -r requirements.txt
# run the code
$ python -m app.main --cfg etc/cfg/dev/eth.json
```

## Requirements
Requirements can be found and should only be modified in `requirements.in`. After updating a requirement make sure to run `pip-compile requirements.in` (from the venv) which creates an updated `requirements.txt` file.