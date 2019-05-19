from flask import (
    Blueprint, render_template, request, url_for, redirect, current_app, abort, flash
)
from PicoEvent.ColorSchema import DefaultColorSchema
from PicoEvent.Database import Database, DatabaseException
from PicoEvent.EventLog import EventLog, EventLogException
from PicoEvent.Environment import Environment
import binascii
import os
import json


admin_blueprint = Blueprint('admin', __name__, url_prefix="/admin")


@admin_blueprint.route('/')
def admin_no_session():
    return render_template("login.jinja2")


@admin_blueprint.route('/api-key/add', methods=['POST'])
def admin_create_api_key():
    with current_app.app_context():
        environment = Environment(current_app)

    session_token = request.form["token"]
    db = Database(logger=current_app.logger, env=environment)
    analyst_user = db.validate_session(session_token)
    if analyst_user and analyst_user.has_permission("create-api-key"):
        new_api_key = binascii.hexlify(os.urandom(8)).decode('utf-8').upper()
        result = db.create_api_key(new_api_key)
        if result == -1:
            flash("Could not create API key.", category="error")
        return redirect(url_for("admin.home",
                                session_token=session_token))
    else:
        abort(403)


@admin_blueprint.route('/<session_token>')
def home(session_token):
    with current_app.app_context():
        environment = Environment(current_app)

    db = Database(logger=current_app.logger, env=environment)
    event_log = EventLog(db, current_app.logger)
    user = db.validate_session(session_token)
    if user:
        event_types = event_log.list_event_types()
        color_schema_css = ""
        color_schema = DefaultColorSchema()
        for x in range(0, len(event_types)):
            rgb = color_schema.rgb(x)
            css = "#event_row_id_{0} {{ background-color: rgb({1},{2},{3}); }}".format(x,
                                                                                       rgb[0],
                                                                                       rgb[1],
                                                                                       rgb[2])
            color_schema_css += css + "\n"
        api_keys = event_log.list_api_keys()
        return render_template("admin_control_panel.jinja2",
                               session_token=session_token,
                               event_types=event_types,
                               api_keys=api_keys,
                               color_schema_css=color_schema_css)
    return redirect(url_for("admin_no_session"))


@admin_blueprint.route('/event-type/add', methods=['POST'])
def add_event_type():
    with current_app.app_context():
        environment = Environment(current_app)

    session_token = request.form['token']
    new_event_name = request.form['new_event_name']

    db = Database(logger=current_app.logger, env=environment)
    user = db.validate_session(session_token)
    if user and user.has_permission("add-event-type"):
        event_log = EventLog(db, current_app.logger)
        try:
            new_event_id = event_log.add_event_type(new_event_name)
            if new_event_id > 0:
                return redirect(url_for("admin.home",
                                        session_token=session_token))
        except EventLogException:
            current_app.logger.error("Event log exception on add_event_type: {0}".format(new_event_name))
            flash("Event log/database exception on add_event_type function.", "error")
            return redirect(url_for("admin.home",
                                    session_token=session_token))
    flash("Not authorized.", category="error")


@admin_blueprint.route('/login', methods=['POST'])
def login():
    with current_app.app_context():
        environment = Environment(current_app)

    input_data = request.get_json(True)

    username = input_data["username"]
    password = input_data["password"]

    db = Database(logger=current_app.logger, env=environment)
    try:
        result = db.login(username, password)
        session_token = result[0]
        return json.dumps({"success": True, "session_token": session_token.decode('utf-8')})
    except DatabaseException:
        flash("Invalid e-mail/password combination.", category="error")
        return json.dumps({"success": False, "error_msg": "Invalid e-mail/password combination."})
