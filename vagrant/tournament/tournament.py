#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#
from random import shuffle
from contextlib import contextmanager

import psycopg2
import itertools


#@contextmanager
def connect(db="tournament"):
    """Connect to the PostgreSQL database.  Returns a database connection."""
    try:
        connection = psycopg2.connect("dbname={}".format(db))
        cursor = connection.cursor()
    except psycopg2.Error:
        print "Could not connect to database: {}".format(db)
        raise

    try:
        yield {'connection': connection, 'cursor': cursor}
    finally:
        connection.close()


def deleteMatches():
    """Remove all the match records from the database."""
    with connect() as database:
        query = "TRUNCATE matches;"
        database['cursor'].execute(query)
        database['connection'].commit()


def deletePlayers():
    """Remove all the player records from the database."""
    with connect() as database:
        query = "DELETE FROM players;"
        database['cursor'].execute(query)
        database['connection'].commit()

def countPlayers():
    """Returns the number of players currently registered."""
    with connect() as database:
        query = "SELECT COUNT(*) FROM players;"
        database['cursor'].execute(query)
        count = database['cursor'].fetchone()[0]

    return count


def registerPlayer(name):
    """Adds a player to the tournament database.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
      name: the player's full name (need not be unique).
    """
    query = "INSERT INTO players (name) VALUES (%s);"
    parameter = (name,)

    with connect() as database:
        database['cursor'].execute(query, parameter)
        database['connection'].commit()

def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    query = ("SELECT num_matches_wins.id, players.name, num_matches_wins.wins, "
            " num_matches_wins.matches "
            "FROM players, num_matches_wins "
            "WHERE players.id = num_matches_wins.id "
            "ORDER BY num_matches_wins.wins desc;")

    with connect() as database:
        database['cursor'].execute(query)
        standings = [(int(row[0]), str(row[1]), int(row[2]), int(row[3]))
                     for row in database['cursor'].fetchall()]

    return standings


def reportMatch(winner, loser=None):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    with connect() as database:
        if loser is None:
            # bye given to winner, and check if winner had bye already
            query = "SELECT had_bye FROM players WHERE id=%s"
            parameter = (winner,)
            database['cursor'].execute(query, parameter)
            had_bye = database['cursor'].fetchone()[0]

            if had_bye is True:
                print "Error: Player has already had a bye."
                return

            # Update had_bye
            query = "UPDATE players SET had_bye=TRUE WHERE id=%s"
            database['cursor'].execute(query, parameter)

    query = "INSERT INTO matches (winner _pid, loser_pid) VALUES (%s, %s);"
    parameter = (winner, loser)
    database['cursor'].execute(query, parameter)
    database['connection'].commit()

def swissPairings():
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
