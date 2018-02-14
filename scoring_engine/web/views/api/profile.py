from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required

import html

from scoring_engine.db import session


from . import mod


@mod.route('/api/profile/update_password', methods=['POST'])
@login_required
def profile_update_password():
    if 'user_id' in request.form and 'password' in request.form:
        if str(current_user.id) == request.form['user_id']:
            current_user.update_password(html.escape(request.form['password']))
            current_user.authenticated = False
            session.add(current_user)
            session.commit()
            flash('Password Successfully Updated.', 'success')
            return redirect(url_for('profile.home'))
        else:
            return {'status': 'Unauthorized'}, 403
    else:
        return {'status': 'Unauthorized'}, 403
