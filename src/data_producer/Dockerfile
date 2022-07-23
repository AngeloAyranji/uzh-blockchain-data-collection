FROM python:3.9

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt requirements.txt
# Install requirements
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "-m", "app.main", "--cfg", "etc/cfg/dev/eth.json" ]
