from enum import IntEnum
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Flask,
    session
)
from werkzeug.exceptions import abort
from .auth import login_required
from .db import get_db
import logging
from .caversham import get_classes, ClassInfo

app = Flask('bookbot')
bp = Blueprint('book', __name__)

app.logger.setLevel(logging.DEBUG)


Weekdays = IntEnum('Weekdays', 'sun mon tue wed thu fri sat', start=0)


@bp.route('/')
def index():
    bookings = None
    db = get_db()
    if g.user and g.user['id']:
        bookings = db.execute(
            'SELECT id, day, times, title, instructor, enabled'
            ' FROM bookings WHERE user_id = ?'
            ' ORDER BY created DESC', (g.user['id'], )
        ).fetchall()

    return render_template('book/index.html', bookings=bookings)


@bp.route('/add_class/<int:new_class>', methods=('GET', 'POST',))
@login_required
def add_to_index(new_class):
    classes = session.get("classes")
    class_info = ClassInfo(**classes[new_class])
    db = get_db()
    db.execute(
                'INSERT INTO bookings (user_id, title, day, times, '
                'instructor, enabled) VALUES (?,?,?,?,?,?)',
                (g.user['id'],
                 class_info.title,
                 class_info.day,
                 class_info.times,
                 class_info.instructor,
                 True)
            )
    db.commit()
    return redirect(url_for('book.index'))


@bp.route('/classes/<int:day>', methods=('GET',))
@login_required
def list_classes(day: Weekdays):
    """List all available classes for a given day of the week"""

    g.day = day
    classes = get_classes(g.day)
    session['classes'] = classes

    return render_template('book/classes.html', classes=classes, day=day)


@bp.route('/toggle_booking/<int:class_id>/<int:enabled>', methods=('GET',))
@login_required
def toggle_booking(class_id, enabled):
    db = get_db()
    db.execute(
        'UPDATE bookings SET enabled = ? WHERE id = ?',
        (enabled, class_id)
    )
    db.commit()
    return redirect(url_for('book.index'))


@bp.route('/<int:class_id>/delete', methods=('GET',))
@login_required
def delete(class_id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    db = get_db()
    db.execute('DELETE FROM bookings WHERE id = ?', (class_id,))
    db.commit()
    return redirect(url_for('book.index'))
