-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

-- Delete previously existing database
DROP DATABASE IF EXISTS tournament;

CREATE DATABASE tournament;

-- Connect to database
\c tournament;

CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);

-- Make fake player if needed for bye games
INSERT INTO players VALUES (0, 'bye game');

CREATE TABLE matches (
	game_id SERIAL PRIMARY KEY,
	winner INT REFERENCES players(id) ON DELETE CASCADE,
	loser INT REFERENCES players(id) ON DELETE CASCADE,
	CHECK (winner <> loser)
);

-- View to see winners
CREATE VIEW wins
AS
	SELECT players.id, players.name, count(matches.winner) AS wins
	FROM players LEFT JOIN matches ON players.id = matches.winner
	WHERE players.id != 0
	GROUP BY players.id, players.name
	ORDER BY wins DESC;
