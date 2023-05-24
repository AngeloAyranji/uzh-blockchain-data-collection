# PostgreSQL database

The `sql` directory contains all init scripts. The default database name is `db`.

## Connecting to the database from command line

1. Download [psql](https://www.postgresql.org/download/)
2. `psql -U user -h localhost -d db` and use the password defined in [.env](.env) or `environment` of the currently used docker compose file.

## Connecting to the database using Docker
`docker exec -it bdc-db-1 psql postgresql://user:postgres@localhost/db`
(see the password and username in [.env](.env))


## Deleting the local data

To delete the local data, just delete `data/postgres-data` in the root directory of this repo.
