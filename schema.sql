CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    url TEXT,
    username TEXT,
    title TEXT,
    avatarUrl TEXT,
    timestamp REAL
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE,
    password TEXT,
    username TEXT
);
