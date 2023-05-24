FROM postgres:15

COPY sql/*.sql /docker-entrypoint-initdb.d/
RUN chmod +rwx /docker-entrypoint-initdb.d/*
