# - Register
# - Login
# - Membuat Post
# - Mendapatkan Semua Post milik seorang User
# - Mendapatkan Detail Post dengan semua yang terkait (Like, dkk)
# - Melakukan Like / Unlike terhadap Post
# - Mengedit Post
# - Menghapus Post

import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask, request, make_response
from queries import CREATE_USERS_TABLE, CREATE_POSTS_TABLE, CREATE_LIKES_TABLE, INSERT_USER, INSERT_POST, INSERT_LIKE, SELECT_POST_BY_USER, SELECT_ALL_POST, DELETE_POST_BY_ID, UPDATE_POST_BY_ID, DELETE_LIKE_BY_USER_POST, SELECT_POST_BY_ID, SELECT_USER_BY_EMAIL
from argon2 import PasswordHasher
from jose import jwt

load_dotenv()

app = Flask(__name__)

url = os.getenv("DATABASE_URL")
connection = psycopg2.connect(url)

ph = PasswordHasher()
secret_key = os.getenv("SECRET_KEY")

# test route
@app.route('/')
def hello():
    return 'Hello World!'

# users route
@app.post('/api/user/register')
def register():
    data = request.get_json()
    email = data['email']
    password = data['password']

    if not email or not password:
        return {"message": "Email and Password Required."}, 400

    try:
        hashed_password = ph.hash(password)
    except Exception as e:
        return {"message": str(e)}, 500

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_USERS_TABLE)
            try:
                cursor.execute(INSERT_USER, (email, hashed_password))
            except psycopg2.Error as e:
                if e.pgcode == psycopg2.errors.UNIQUE_VIOLATION:
                    return {"message": "Email already in use."}, 409
                
                return {"message": str(e)}, 500
    
    token = jwt.encode({"payload": data}, secret_key, algorithm='HS256')
    response = make_response({"message": f"User {email} successfully created."}, 201)
    response.set_cookie('access_token', token)
    return response

@app.post('/api/user/login')
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_USER_BY_EMAIL, (email,))
            result = cursor.fetchone()

            if result is None:
                return {"message": "Invalid email."}, 401
            else:
                hashed_password = result[0]

                if ph.verify(hashed_password, password):
                    token = jwt.encode({"payload": data}, secret_key, algorithm='HS256')
                    response = make_response({"message": "Login success."}, 200)
                    response.set_cookie('access_token', token)
                    return response
                else:
                    return {"message":"Invalid password."}, 401

# posts route
@app.post('/api/post')
def create_post():
    data = request.get_json()
    content = data["content"]
    user_id = data["user_id"]

    if not content or not user_id:
        return {"message": "Content and User ID Required."}, 400

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_POSTS_TABLE)
            try:
                cursor.execute(INSERT_POST, (content, user_id))
            except psycopg2.Error as e:
                return {"message": str(e)}, 500

    return {"message": f"Post successfully created."}, 201

@app.get('/api/post')
def get_all_post():
    with connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(SELECT_ALL_POST)
                posts = cursor.fetchall()
            except psycopg2.Error as e:
                return {"message": str(e)}, 500

            post_list = []
            for post in posts:
                post_data = {
                    'id': post[0],
                    'content': post[1],
                    'user_id': post[2],
                    'total_likes': post[3]
                }
                post_list.append(post_data)
            
            return {"posts": post_list}, 200

@app.get('/api/post/<int:user_id>')
def get_user_post(user_id):
    with connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(SELECT_POST_BY_USER, (user_id,))
                posts = cursor.fetchall()
            except psycopg2.Error as e:
                return {"message": str(e)}, 500
            
            if posts:
                post_list = []
                for post in posts:
                    post_data = {
                        'id': post[0],
                        'content': post[1],
                        'user_id': post[2],
                        'total_likes': post[3]
                    }
                    post_list.append(post_data)
                
                return {"posts": post_list}, 200
            else:
                return {"message": "Post Not Found."}, 404

@app.delete('/api/post/<int:post_id>')
def delete_post(post_id):
    with connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(DELETE_POST_BY_ID, (post_id,))
                if cursor.rowcount == 0:
                    return {"message": "Post not found."}, 404
            except psycopg2.Error as e:
                return {"message": str(e)}, 500
            
            return {"message": "Post deleted successfully."}, 200
        
@app.patch('/api/post/<int:post_id>')
def update_post(post_id):
    data = request.get_json()
    content = data['content']

    if not content:
        return {"message": "Content is required"}, 400

    with connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(UPDATE_POST_BY_ID, (content, post_id))
                if cursor.rowcount == 0:
                    return {"message": "Post not found."}, 404
            except psycopg2.Error as e:
                return {"message": str(e)}, 500
            
            return {"message": "Post updated successfully."}, 200


# likes route
@app.post('/api/post/<int:post_id>/like')
def like(post_id):
    data = request.get_json()
    user_id = data["user_id"]

    if not user_id:
        return {"message": "User ID Required."}, 400

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_LIKES_TABLE)

            cursor.execute(SELECT_POST_BY_ID, (post_id,))
            post = cursor.fetchone()

            if not post:
                return {"message": "Post not found."}, 404

            try:
                cursor.execute(INSERT_LIKE, (user_id, post_id))
            except psycopg2.Error as e:
                return {"message": str(e)}, 500

    return {"message": f"Post liked successfully."}, 201

@app.delete('/api/post/<int:post_id>/like')
def dislike(post_id):
    data = request.get_json()
    user_id = data["user_id"]

    if not user_id:
        return {"message": "User ID Required."}, 400

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_POST_BY_ID, (post_id,))
            post = cursor.fetchone()

            if not post:
                return {"message": "Post not found."}, 404

            try:
                cursor.execute(DELETE_LIKE_BY_USER_POST, (user_id, post_id))
            except psycopg2.Error as e:
                return {"message": str(e)}, 500
    
    return {"message": "Post unliked successfully."}, 200

if __name__ == '__main__':
    app.run(debug=True)