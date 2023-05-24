# Data Collection containers
Code for building producer and consumer docker containers. The code between these containers is shared and only an input argument (`--worker-type`) into the main module determines whether a producer or consumer is started:

```
# Start an ETH data producer
$ python -m app.main --cfg etc/cfg/dev/eth.json --worker-type producer

# Start an ETH data consumer
$ $ python -m app.main --cfg etc/cfg/dev/eth.json --worker-type consumer
```

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
# create a virtual environment from this directory (src/data_collection)
$ python -m venv venv
# activate it
$ source ./venv/bin/activate
# install requirements
(venv) $ pip install -r requirements.txt
# run the code
$ python -m app.main --cfg etc/cfg/dev/eth.json --worker-type producer
```

## Requirements
Requirements can be found and should only be modified in `requirements.in`. After updating a requirement make sure to run `pip-compile requirements.in` (from the venv) which creates an updated `requirements.txt` file.

## Configuration
The app requires a configuration file to be passed into the main module with an input argument (`--cfg`). A description of each of the values inside any `etc/cfg/<config>.json` file can be found in [app/config.py](app/config.py)

## Testing

The tests can be found in the `tests/` directory. Currently only the `db/manager.py` class is tested.

The recommended way to start the tests is to use the `scripts/tests/run-tests-db.sh` script in the root of this repository.
