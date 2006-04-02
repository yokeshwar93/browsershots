CREATE TABLE person (
person SERIAL PRIMARY KEY NOT NULL,
name VARCHAR(20) NOT NULL UNIQUE,
email VARCHAR(60) NOT NULL UNIQUE,
created TIMESTAMP DEFAULT NOW());

CREATE TABLE engine (
engine SERIAL PRIMARY KEY NOT NULL,
name VARCHAR(20),
created TIMESTAMP DEFAULT NOW(),
creator INT NOT NULL REFERENCES person);

CREATE TABLE browser (
browser SERIAL PRIMARY KEY NOT NULL,
name VARCHAR(20) NOT NULL UNIQUE,
manufacturer VARCHAR(20),
terminal BOOLEAN NOT NULL DEFAULT FALSE,
created TIMESTAMP DEFAULT NOW(),
creator INT NOT NULL REFERENCES person);

CREATE TABLE browser_version (
browser_version SERIAL PRIMARY KEY NOT NULL,
browser INT NOT NULL REFERENCES browser,
major INT NOT NULL,
minor INT,
engine INT REFERENCES engine,
created TIMESTAMP DEFAULT NOW(),
creator INT NOT NULL REFERENCES person);

CREATE TABLE os (
os SERIAL PRIMARY KEY NOT NULL,
name VARCHAR(20) NOT NULL,
manufacturer VARCHAR(20),
mobile BOOLEAN NOT NULL DEFAULT FALSE,
created TIMESTAMP DEFAULT NOW(),
creator INT NOT NULL REFERENCES person);

CREATE TABLE os_version (
os_version SERIAL PRIMARY KEY NOT NULL,
os INT NOT NULL REFERENCES os,
distro VARCHAR(20),
codename VARCHAR(20),
major INT,
minor INT,
created TIMESTAMP DEFAULT NOW(),
creator INT NOT NULL REFERENCES person);

CREATE TABLE factory (
factory SERIAL PRIMARY KEY NOT NULL,
name VARCHAR(20) NOT NULL UNIQUE,
os_version INT NOT NULL REFERENCES os_version,
created TIMESTAMP DEFAULT NOW(),
creator INT NOT NULL REFERENCES person,
last_poll TIMESTAMP,
last_upload TIMESTAMP);

CREATE TABLE factory_browser (
factory INT NOT NULL REFERENCES factory,
browser_version INT NOT NULL REFERENCES browser_version);

CREATE TABLE factory_screen (
factory INT NOT NULL REFERENCES factory,
width INT NOT NULL,
height INT NOT NULL);

CREATE TABLE screenshot (
screenshot SERIAL PRIMARY KEY NOT NULL,
factory INT NOT NULL REFERENCES factory,
width INT NOT NULL,
height INT NOT NULL,
created TIMESTAMP DEFAULT NOW());

CREATE TABLE website (
website SERIAL PRIMARY KEY NOT NULL,
url VARCHAR(255) NOT NULL UNIQUE CHECK (url LIKE 'http://%'),
created TIMESTAMP DEFAULT NOW());

CREATE TABLE request (
request SERIAL PRIMARY KEY NOT NULL,
website INT NOT NULL,
browser INT NOT NULL REFERENCES browser,
major INT,
minor INT,
width INT,
os INT,
screenshot INT REFERENCES screenshot,
created TIMESTAMP DEFAULT NOW(),
creator INT REFERENCES person);

CREATE TABLE lock (
request INT NOT NULL REFERENCES request,
factory INT NOT NULL REFERENCES factory,
created TIMESTAMP DEFAULT NOW());
