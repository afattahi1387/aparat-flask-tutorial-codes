import datetime
import jdatetime
import sqlite3
import config

def db_connect():
    return sqlite3.connect(config.DATABASE_PATH)

def create_tables():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image TEXT NOT NULL,
            description TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            date DATE,
            action INTEGER NOT NULL,
            delete_date DATE
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            comment TEXT NOT NULL,
            article_id INTEGER NOT NULL,
            answer_to INTEGER NULL,
            date DATE NOT NULL
        );
    """)
    conn.commit()
    conn.close()

create_tables()

def get_all_categories():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories")
    return cur.fetchall()

def get_category_with_id(id):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM categories WHERE id = {id}")
    return cur.fetchone()

def check_category_exists(value_type, value):
    cur = db_connect().cursor()
    if value_type == 'id':
        cur.execute(f"SELECT * FROM categories WHERE id = {value}")
    elif value_type == 'name':
        cur.execute(f"SELECT * FROM categories WHERE category_name = '{value}'")
    if not cur.fetchone():
        return False
    return True

def insert_category(new_category_name):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"INSERT INTO categories VALUES (NULL, '{new_category_name}')")
    conn.commit()
    conn.close()

def update_category(category_id, new_category_name):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"UPDATE categories SET category_name = '{new_category_name}' WHERE id = {category_id}")
    conn.commit()
    conn.close()

def delete_category(category_id):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM categories WHERE id = {category_id}")
    conn.commit()
    conn.close()

def get_all_articles(action = 1, order_by = 'id'):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM articles WHERE action = '{action}' ORDER BY {order_by} DESC")
    return cur.fetchall()

def get_articles_with_category_id(category_id, action = 1):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM articles WHERE category_id = '{category_id}' AND action = '{action}' ORDER BY id DESC")
    return cur.fetchall()

def get_articles_with_search(searched_word):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM articles WHERE name LIKE '%{searched_word}%' OR description LIKE '%{searched_word}%' ORDER BY id DESC") #TODO: add check article action.
    results = cur.fetchall()
    if not results:
        return False
    return results

def get_article_with_id(id, action = 1):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM articles WHERE id = {id} AND action = '{action}'")
    result = cur.fetchone()
    if not result:
        return False
    return result

def get_all_articles_with_counter(action = 1, order_by = 'id'):
    all_articles = get_all_articles(action, order_by)
    articles = {}
    counter = 0
    for article in all_articles:
        article = list(article)
        article[4] = get_category_with_id(article[4])[1]
        counter += 1
        articles[counter] = article
    
    return articles

def get_comment_with_id(comment_id):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM comments WHERE id = {comment_id}")
    result = cur.fetchone()
    conn.commit()
    conn.close()
    return result

def get_article_comments(article_id):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM comments WHERE article_id = {article_id}")
    results = cur.fetchall()
    conn.commit()
    conn.close()
    if not results:
        return False
    comments = []
    for i in results:
        i = list(i)
        if i[4]:
            i.append(get_comment_with_id(i[4])[1])
        comments.append(i)
    return comments

def insert_comment(information):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"INSERT INTO comments VALUES (NULL, '{information['user_name']}', '{information['comment']}', '{information['article_id']}', {information['answer_to']}, '{information['date']}')")
    conn.commit()
    conn.close()

def get_current_time():
    return jdatetime.datetime.fromgregorian(datetime=datetime.datetime.now()).strftime('%Y-%m-%d %H:%M:%S')

def insert_article(information):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"""
        INSERT INTO articles VALUES
        (NULL, '{information['name']}', '{information['image_filename']}', '{information['description']}', '{information['category']}', '{information['full_time']}', '1', NULL);
    """)
    inserted_article_id = cur.lastrowid
    conn.commit()
    conn.close()
    return str(inserted_article_id)

def update_article(article_id, information):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"""UPDATE articles SET
        name = '{information['name']}',
        description = '{information['description']}',
        category_id = '{information['category']}'
        WHERE id = {article_id}""")
    conn.commit()
    conn.close()

def transfer_article_to_trash(article_id):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"UPDATE articles SET action = 0, delete_date = '{get_current_time()}' WHERE id = {article_id}")
    conn.commit()
    conn.close()

def allow_to_files(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in config.ALLOWED_FILES_EXTENSIONS

def update_article_image_name(article_id, new_article_image_name):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"UPDATE articles SET image = '{new_article_image_name}' WHERE id = {article_id}")
    conn.commit()
    conn.close()

def restore_article_from_trash(article_id):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"UPDATE articles SET action = 1, delete_date = NULL WHERE id = {article_id}")
    conn.commit()
    conn.close()

def delete_article(article_id):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM articles WHERE id = {article_id}")
    #TODO: delete_comments
    conn.commit()
    conn.close()
