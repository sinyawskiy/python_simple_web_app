#!../env/bin/python
# coding=utf-8
import os
import sqlite3
from string import Template
import urllib
from wsgiref.simple_server import make_server
import sys
import re
from cgi import escape

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = 'sqlite.db'
CONNECTION = sqlite3.connect(os.path.join(CURRENT_DIR, DATABASE_NAME))
CONNECTION.cursor().execute('''
DROP TABLE IF EXISTS todo;
''')
CONNECTION.commit()
CONNECTION.cursor().execute('''
CREATE TABLE todo(
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   COMMENT TEXT NOT NULL
);
''')


def not_found(environ, start_response):
    start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
    return ['Not Found']


def template_not_found(environ, start_response):
    start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
    return ['Template not Found']


# todo list
def index(environ, start_response, saved=False):
    row = CONNECTION.cursor().execute('''
        SELECT id, comment
        FROM todo;
    ''')
    comments_qs = row.fetchall()
    CONNECTION.commit()

    comments = u''.join([u'<tr><td>%s</td><td>%s</td><td><a href="/delete/%s">Удалить</a></td>' %( item[0], item[1], item[0]) for item in comments_qs])
    try:
        with open('templates/index.html') as template_file:
            template = Template(template_file.read())
    except IOError:
        return template_not_found(environ, start_response)

    start_response('200 OK', [('Content-Type', 'text/html')])
    return [template.substitute({'comments': comments.encode('utf-8'), 'saved': '<div>Ваш комментарий добавлен</div>' if saved else ''})]


# Add comment
def comment(environ, start_response):
    if environ['REQUEST_METHOD'] == 'POST':
        try:
            request_body_size = int(environ['CONTENT_LENGTH'])
            request_body = environ['wsgi.input'].read(request_body_size).split('\n')
        except (TypeError, ValueError):
            request_body = []
        else:
            post_values = dict(item.split('=') for item in request_body)
            post_values['comment'] = urllib.unquote_plus(post_values['comment'])

            row = CONNECTION.cursor().execute('''
                INSERT INTO todo(comment) VALUES("%s");
            ''' % post_values['comment']
            )
        return index(environ, start_response, saved=True)
    else:
        try:
            with open('templates/comment.html') as template_file:
                template = Template(template_file.read())
        except IOError:
            return template_not_found(environ, start_response)

        start_response('200 OK', [('Content-Type', 'text/html')])
        return [template.substitute({})]


# Delete comment
def delete(environ, start_response):
    args = environ['url_args']
    if args:
        print args[0]
        CONNECTION.cursor().execute('''
            DELETE FROM todo WHERE id=%s;
        ''' % args[0])
        CONNECTION.commit()
    return index(environ, start_response)


# Map
urls = [
    (r'^$', index),
    (r'add/?$', comment),
    (r'delete/(.+)$', delete),
]


def application(environ, start_response):
    path = environ.get('PATH_INFO', '').lstrip('/')
    for regex, callback in urls:
        match = re.search(regex, path)
        if match is not None:
            environ['url_args'] = match.groups()
            return callback(environ, start_response)
    return not_found(environ, start_response)


if __name__ == '__main__':
    srv = make_server('localhost', 8080, application)
    sys.exit(srv.serve_forever())