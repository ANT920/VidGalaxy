CREATE TABLE videos (
    id INTEGER PRIMARY KEY,
    url TEXT,
    username TEXT,
    title TEXT,
    avatarUrl TEXT,
    timestamp REAL
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE,
    password TEXT,
    username TEXT
);
