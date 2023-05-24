-- creating a table func -> https://dba.stackexchange.com/a/42930
-- ERC20 properties -> https://eips.ethereum.org/EIPS/eip-20
-- ERC721 properties -> https://eips.ethereum.org/EIPS/eip-721
-- ERC 1155 properties -> https://eips.ethereum.org/EIPS/eip-1155
-- uint256 data type in postgreSQL as numeric(78,0) -> https://stackoverflow.com/questions/50072618/how-to-create-an-uint256-in-postgresql
-- but we agreed on varchar() for address.
-- beware of the python and postgreSQL datatype conventions.
-- in python int32 = 32 bit
-- in postgres int4 = 4 bytes = 32 bit
--address varchar()PRIMARY KEY,              #uint256
--symbol varchar(128),
--name varchar(),
--decimals int,                                   #int8
--total_supply numeric(78,0),                     #uint256
--block_timestamp timestamp,                      #without time zone
--block_number bigint,
-- CONTRACT TABLE
-- since not every contract is a token, we create a separate table for all the contract data.
CREATE OR REPLACE FUNCTION create_table_contract(blockchain_name varchar(30))
   RETURNS VOID
   LANGUAGE plpgsql
   AS $func$
BEGIN
   EXECUTE format('
      CREATE TABLE IF NOT EXISTS %I (
       address varchar PRIMARY KEY,
       transaction_hash varchar,
       is_pair_contract boolean
      )', blockchain_name || '_contract');
END
$func$;

SELECT
   create_table_contract('bsc');

SELECT
   create_table_contract('eth');

SELECT
   create_table_contract('etc');

-- TOKEN CONTRACT TABLE - ERC20 & ERC721 & ERC1155
CREATE OR REPLACE FUNCTION create_table_token_contract(blockchain_name varchar(30))
   RETURNS VOID
   LANGUAGE plpgsql
   AS $func$
BEGIN
   EXECUTE format('
      CREATE TABLE IF NOT EXISTS %I (
       address varchar PRIMARY KEY REFERENCES %I(address),
       symbol varchar,
       name varchar,
       decimals int,
       total_supply numeric(78,0),
       token_category varchar
      )', blockchain_name || '_token_contract', blockchain_name || '_contract');
END
$func$;

SELECT
   create_table_token_contract('eth');

SELECT
   create_table_token_contract('bsc');

SELECT
   create_table_token_contract('etc');

-- TOKEN CONTRACT TABLE - ERC20 & ERC721 & ERC1155
CREATE OR REPLACE FUNCTION create_table_nft_transfer(blockchain_name varchar(30))
   RETURNS VOID
   LANGUAGE plpgsql
   AS $func$
BEGIN
   EXECUTE format('
      CREATE TABLE IF NOT EXISTS %I (
       transaction_hash varchar,
       log_index int,
       address varchar,
       to_address varchar,
       from_address varchar,
       token_id numeric(78,0),
       PRIMARY KEY(transaction_hash, log_index)
      )', blockchain_name || '_nft_transfer', blockchain_name || '_contract');
END
$func$;

SELECT
   create_table_nft_transfer('eth');

SELECT
   create_table_nft_transfer('bsc');

SELECT
   create_table_nft_transfer('etc');

--CONTRACT SUPPLY CHANGE TABLE
CREATE OR REPLACE FUNCTION create_table_contract_supply_change(blockchain_name varchar(30))
   RETURNS VOID
   LANGUAGE plpgsql
   AS $func$
BEGIN
   EXECUTE format('
      CREATE TABLE IF NOT EXISTS %I(
       address varchar,
       amount_changed numeric(78,0),
       transaction_hash varchar,
       PRIMARY KEY(address, transaction_hash)
   )', blockchain_name || '_contract_supply_change');
END
$func$;

SELECT
   create_table_contract_supply_change('eth');

SELECT
   create_table_contract_supply_change('bsc');

SELECT
   create_table_contract_supply_change('etc');

---PAIR CONTRACT TABLE---
CREATE OR REPLACE FUNCTION create_table_pair_contract(blockchain_name varchar(30))
   RETURNS VOID
   LANGUAGE plpgsql
   AS $func$
BEGIN
   EXECUTE format('
      CREATE TABLE IF NOT EXISTS %I(
       address varchar PRIMARY KEY REFERENCES %I(address),
       token0_address varchar,
       token1_address varchar,
       reserve0 numeric(78,0),
       reserve1 numeric(78,0),
       factory varchar
   )', blockchain_name || '_pair_contract', blockchain_name || '_contract');
END
$func$;

SELECT
   create_table_pair_contract('eth');

SELECT
   create_table_pair_contract('bsc');

SELECT
   create_table_pair_contract('etc');

--CONTRACT SUPPLY CHANGE TABLE
CREATE OR REPLACE FUNCTION create_table_pair_liquidity_change(blockchain_name varchar(30))
   RETURNS VOID
   LANGUAGE plpgsql
   AS $func$
BEGIN
   EXECUTE format('
      CREATE TABLE IF NOT EXISTS %I(
       address varchar,
       amount0 numeric(78,0),
       amount1 numeric(78,0),
       transaction_hash varchar,
       PRIMARY KEY(address, transaction_hash)
   )', blockchain_name || '_pair_liquidity_change');
END
$func$;

SELECT
   create_table_pair_liquidity_change('eth');

SELECT
   create_table_pair_liquidity_change('bsc');

SELECT
   create_table_pair_liquidity_change('etc');

