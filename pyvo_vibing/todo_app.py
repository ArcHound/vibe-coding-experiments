#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for
from flask import g

import os
if not os.path.exists('templates'):
    os.makedirs('templates')
      

app = Flask(__name__)


import sqlite3


def create_table():
    db = sqlite3.connect('todos.db')
    cursor = db.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS todos (
                        id INTEGER PRIMARY KEY,
                        task TEXT NOT NULL)''')
    db.commit()


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('todos.db')
        g.cursor = g.db.cursor()
    return g.db, g.cursor

@app.teardown_appcontext
def close_db(error):
    if 'db' in g:
        g.db.close()


def get_todos():
    db, cursor = get_db()
    cursor.execute('SELECT * FROM todos')
    rows = cursor.fetchall()
    return [{'id': row[0], 'task': row[1]} for row in rows]

@app.route('/')
def index():
    todos = get_todos()
    return render_template('index.html', todos=todos)


@app.route('/add', methods=['POST'])
def add_todo():
    db, cursor = get_db()
    todo = request.form['todo']
    cursor.execute('SELECT MAX(id) FROM todos')
    max_id = cursor.fetchone()[0]
    new_id = 1 if max_id is None else max_id + 1
    cursor.execute('INSERT INTO todos (id, task) VALUES (?, ?)', (new_id, todo))
    db.commit()
    return redirect(url_for('index'))



@app.route('/delete/<int:index>')
def delete_todo(index):
    db, cursor = get_db()
    cursor.execute('DELETE FROM todos WHERE id = ?', (index,))
    db.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

