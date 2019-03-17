from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Flask
)
from werkzeug.exceptions import abort
from .auth import login_required
from .db import get_db
import logging
from .caversham import get_classes, Weekdays

app = Flask(__name__)
bp = Blueprint('book', __name__)

app.logger.setLevel(logging.INFO)

@bp.route('/')
def index():
    """Show currently selected list of exercise classes"""
    db = get_db()
    bookings = db.execute(
        'SELECT id, time, title, instructor'
        ' FROM bookings ORDER BY created DESC'
    ).fetchall()
    return render_template('book/index.html', bookings=bookings)


def toggle_booking(id, enabled):
    """enable / disable on of the saved booking schedules

    # TODO
    :param id: id of the booking
    :param enabled: current state
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:new_class>/add_class', methods=('POST',))
@login_required
def add_to_index(new_class):
    # todo need to work out how to link int to a ClassInfo
    pass


@bp.route('/<int:day>/classes', methods=('GET',))
@login_required
def classes(day: Weekdays):
    """List all available classes for a given day of the week"""

    g.day = day
    classes = get_classes(g.day)

    return render_template('book/classes.html', classes=classes)
    # if request.method == 'POST':
    #     title = request.form['title']
    #     body = request.form['body']
    #     error = None
    #
    #     if not title:
    #         error = 'Title is required.'
    #
    #     if error is not None:
    #         flash(error)
    #     else:
    #         db = get_db()
    #         db.execute(
    #             'INSERT INTO post (title, body, author_id)'
    #             ' VALUES (?, ?, ?)',
    #             (title, body, g.user['id'])
    #         )
    #         db.commit()
    #         return redirect(url_for('book.index'))


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ? WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('book.index'))

    return render_template('book/add_class.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('book.index'))
