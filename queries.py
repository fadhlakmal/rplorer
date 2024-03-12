CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL
);
"""

CREATE_POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS posts (
  id SERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE
);
"""

CREATE_LIKES_TABLE = """
CREATE TABLE IF NOT EXISTS likes (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  post_id INT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  UNIQUE (user_id, post_id)
);
"""

INSERT_USER = """
INSERT INTO users (email, password)
VALUES (%s, %s);
"""

INSERT_POST = """
INSERT INTO posts (content, user_id)
VALUES (%s, %s);
"""

INSERT_LIKE = """
INSERT INTO likes (user_id, post_id)
VALUES (%s, %s);
"""

SELECT_POST_BY_USER = """
SELECT p.id, p.content, p.user_id, COUNT(l.id) as total_likes FROM posts P
LEFT JOIN likes l ON p.id = l.post_id 
WHERE p.user_id = %s 
GROUP BY p.id;
"""

SELECT_ALL_POST = """
SELECT p.id, p.content, p.user_id, COUNT(l.id) as total_likes
FROM posts p
LEFT JOIN likes l ON p.id = l.post_id
GROUP BY p.id;
"""

DELETE_POST_BY_ID = """
DELETE FROM posts WHERE id = %s;
"""

UPDATE_POST_BY_ID = """
UPDATE posts SET content = %s WHERE id = %s;
"""

DELETE_LIKE_BY_USER_POST = """
DELETE FROM likes WHERE user_id = %s AND post_id = %s;
"""

SELECT_POST_BY_ID = """
SELECT * FROM posts WHERE id = %s;
"""

SELECT_USER_BY_EMAIL = """
SELECT password FROM users WHERE email = %s;
"""
