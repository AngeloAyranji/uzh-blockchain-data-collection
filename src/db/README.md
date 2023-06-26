# PostgreSQL database

The `sql` directory contains all init scripts. The default database name is `db`.

## Connecting to the database using Docker

```
$ docker exec -it bdc-db-1 psql postgresql://user:postgres@localhost/db
```
The name of the container can be different (e.g. because of `PROJECT_NAME` variable or dev environment), please check `docker ps` for the correct name and whether it is running. If the container is shut down, just run [scripts/run-db.sh](/scripts/run-db.sh) first.

(see the password and username in [.env](.env))

After connecting to the container, simply execute any SQL queries.

## Connecting to the database from command line

1. Download [psql](https://www.postgresql.org/download/)
2. `psql -U user -h localhost -d db` and use the password defined in [.env](.env) or `environment` of the currently used docker compose file.

## Deleting the local data

To delete the local data, just delete `$DATA_DIR/postgresql-data/`.
