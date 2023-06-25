-- https://dba.stackexchange.com/a/42930
CREATE OR REPLACE FUNCTION create_table_block(node_name varchar(3))
  RETURNS VOID
  LANGUAGE plpgsql
  AS $func$
BEGIN
  EXECUTE format('
      CREATE TABLE IF NOT EXISTS %I (
       block_number bigint PRIMARY KEY,
       block_hash varchar,
       nonce varchar,
       difficulty numeric(78,0),
       gas_limit bigint,
       gas_used bigint,
       timestamp timestamp,
       miner varchar,
       parent_hash varchar,
       block_reward numeric(78,18),
       uncles varchar ARRAY,
       updated_at TIMESTAMP
      )', node_name || '_block');
END
$func$;

SELECT
  create_table_block('eth');

SELECT
  create_table_block('etc');

SELECT
  create_table_block('bsc');

CREATE OR REPLACE FUNCTION create_table_transaction(node_name varchar(3))
  RETURNS VOID
  LANGUAGE plpgsql
  AS $func$
BEGIN
  EXECUTE format('
      CREATE TABLE IF NOT EXISTS %I (
       transaction_hash varchar PRIMARY KEY,
       block_number bigint,
       from_address varchar,
       to_address varchar,
       value numeric(78,18),
       transaction_fee numeric(78,18),
       gas_price numeric(78,18),
       gas_limit numeric(78,0),
       gas_used numeric(78,0),
       is_token_tx boolean,
       input_data varchar,
       updated_at TIMESTAMP
      )', node_name || '_transaction');
END
$func$;

SELECT
  create_table_transaction('eth');

SELECT
  create_table_transaction('etc');

SELECT
  create_table_transaction('bsc');

CREATE OR REPLACE FUNCTION create_table_internal_transaction(node_name varchar(3))
  RETURNS VOID
  LANGUAGE plpgsql
  AS $func$
BEGIN
  EXECUTE format('
    CREATE TABLE IF NOT EXISTS %I (
      transaction_hash varchar,
      from_address varchar,
      to_address varchar,
      value numeric(78,18),
      gas_limit bigint,
      gas_used bigint,
      input_data varchar,
      call_type varchar,
      updated_at TIMESTAMP
    )', node_name || '_internal_transaction');
  EXECUTE format('
    CREATE INDEX IF NOT EXISTS %I
    ON %I (transaction_hash)', node_name || '_internal_transaction_transaction_hash_idx', node_name || '_internal_transaction');
END
$func$;

SELECT
  create_table_internal_transaction('eth');

SELECT
  create_table_internal_transaction('etc');

SELECT
  create_table_internal_transaction('bsc');

CREATE OR REPLACE FUNCTION create_table_transaction_logs(node_name varchar(3))
  RETURNS VOID
  LANGUAGE plpgsql
  AS $func$
BEGIN
  EXECUTE format('
      CREATE TABLE IF NOT EXISTS %I (
       transaction_hash varchar,
       address varchar,
       log_index int,
       data varchar,
       removed boolean,
       topics varchar ARRAY,
       updated_at TIMESTAMP,
       PRIMARY KEY (transaction_hash, log_index)
      )', node_name || '_transaction_logs');
END
$func$;

SELECT
  create_table_transaction_logs('eth');

SELECT
  create_table_transaction_logs('etc');

SELECT
  create_table_transaction_logs('bsc');

-- Add updated_at trigger for all tables in this file
-- ujebane Memonilovi, dakujeme za kus dobrej roboty
CREATE OR REPLACE FUNCTION set_updated_at()
  RETURNS TRIGGER
  AS $$
BEGIN
  NEW.updated_at = now() at time zone 'utc';
  RETURN NEW;
END;
$$
LANGUAGE 'plpgsql';

DO $$
DECLARE
  t text;
BEGIN
  FOR t IN
  SELECT
    table_name
  FROM
    information_schema.tables
  WHERE
    table_schema = 'public'
    AND table_name LIKE ANY (ARRAY['%_transaction', '%_block', '%_transaction_logs', '%_internal_transaction'])
      LOOP
        EXECUTE format('
      CREATE TRIGGER set_updated_at_on_insert
      BEFORE INSERT on %I
      FOR EACH ROW
      EXECUTE PROCEDURE set_updated_at()
    ', t);
        EXECUTE format('
      CREATE TRIGGER set_updated_at
      BEFORE UPDATE on %I
      FOR EACH ROW
      EXECUTE PROCEDURE set_updated_at()
    ', t);
      END LOOP;
END;
$$
LANGUAGE plpgsql;
