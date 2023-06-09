CREATE TABLE currency_rates
	(
	id serial PRIMARY KEY UNIQUE,
	base_currency varchar(3) NOT NULL
	);

CREATE TABLE currency_rates_values
	(
	id serial PRIMARY KEY UNIQUE,
	base_currency varchar(3) NOT NULL,
	rate numeric NOT NULL,
	currency_rate_id integer REFERENCES currency_rates(id)
	);

CREATE TABLE admins
	(
	id integer PRIMARY KEY UNIQUE,
	chat_id varchar
	);

INSERT INTO admins(id, chat_id) VALUES (1,'388930488');