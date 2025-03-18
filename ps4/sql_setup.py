# Code that should be run ONLY to set up the database for the first time

import sqlite3

sqliteConnection = sqlite3.connect('server.db')
cursor = sqliteConnection.cursor()

# Creates table for users
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
username TEXT PRIMARY KEY,
password TEXT NOT NULL);""")
sqliteConnection.commit()

# Creates table for messages
cursor.execute("""CREATE TABLE IF NOT EXISTS messages (
  message_id INTEGER PRIMARY KEY,
  recipient_username TEXT,
  message TEXT,
  timestamp TEXT,
  instant INTEGER,
  delivered INTEGER,
  FOREIGN KEY (recipient_username)
       REFERENCES users (username)
);""")
sqliteConnection.commit()

# Close connection
sqliteConnection.close()