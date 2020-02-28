DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS comments;
DROP TABLE iF EXISTS users;

CREATE TABLE posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT,
  video TEXT,
  image TEXT,
  votes INTEGER NOT NULL,
  username TEXT NOT NULL,
  FOREIGN KEY(author_id) REFERENCES users(id),
  FOREIGN KEY(username) REFERENCES users(username)
);

CREATE TABLE comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  body TEXT,
  post INTEGER NOT NULL,
  parent INTEGER,
  votes INTEGER NOT NULL,
  level INTEGER NOT NULL,
  username TEXT NOT NULL,
  FOREIGN KEY(post) REFERENCES posts(id),
  FOREIGN KEY(id) REFERENCES comments(id),
  FOREIGN KEY(author_id) REFERENCES users(id),
  FOREIGN KEY(username) REFERENCES users(username)
);

CREATE TABLE users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  username TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL
);