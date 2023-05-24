FROM python:3.11

VOLUME "/app/etc"

ENV LOG_LEVEL=INFO
ENV N_CONSUMER_INSTANCES=5
ENV SENTRY_DSN=
ENV WEB3_REQUESTS_TIMEOUT=30
ENV WEB3_REQUESTS_RETRY_LIMIT=10
ENV WEB3_REQUESTS_RETRY_DELAY=5
ENV KAFKA_EVENT_RETRIEVAL_TIMEOUT=900

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt requirements.txt
# Install requirements
RUN pip install -r requirements.txt

COPY app app
COPY scripts/wait-for-kafka.sh wait-for-kafka.sh

RUN chmod +x wait-for-kafka.sh

CMD [ "python3", "-m", "app.main", "--cfg", "etc/cfg/dev/eth.json", "--worker-type", "producer" ]
