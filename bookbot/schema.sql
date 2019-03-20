-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS bookings;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE bookings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  day TEXT NOT NULL,
  times TEXT NOT NULL,
  instructor TEXT NOT NULL,
  enabled INTEGER NOT NULL,
  booked INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user (id)
);
