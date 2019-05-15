from flask import (
    Blueprint, request, current_app, Response, abort
)

from PicoEvent.EventLog import EventLog, APIKeyInvalid, APIKeyRateLimited, APIKeySuspended
from PicoEvent.Database import Database
from PicoEvent.Environment import Environment
import json
import re

EVENT_TYPE_REGEX = re.compile("[\w\-\s]{5,50}")

rest_blueprint = Blueprint('api', __name__, url_prefix="/api")


@rest_blueprint.route('/<api_key>', methods=['POST'])
def post_event(api_key):
    with current_app.app_context():
        environment = Environment(current_app.config["MYSQL_HOST"],
                                  current_app.config["MYSQL_READ_ONLY_HOST"],
                                  current_app.config["MYSQL_USER"],
                                  current_app.config["MYSQL_PASSWORD"],
                                  current_app.config["MYSQL_DB"],
                                  current_app.config["MYSQL_TEST_DB"],
                                  current_app.config["RATE_LIMIT_QUOTA"],
                                  current_app.config["RATE_LIMIT_RESET"],
                                  current_app.config["REDIS_MASTER_HOST"],
                                  current_app.config["REDIS_READ_ONLY_HOST"])

    db = Database(logger=current_app.logger, env=environment)
    event_log = EventLog(db, logger=current_app.logger)
    try:
        node = event_log.get_api_key_object(api_key)
        event_log.update_quota(node)
        posted_data = request.get_json(force=True)
        if "event_type_id" in posted_data:
            event_type_id = int(posted_data["event_type_id"])
            if event_type_id in event_log.event_type_ids_as_set:
                node_id = node.node_id
                user_id = None
                if "user_id" in posted_data and posted_data["user_id"] is not None:
                    user_id = int(posted_data["user_id"])
                    del posted_data["user_id"]
                    if user_id <= 0:
                        raise ValueError("user_id must be positive or omitted")
                new_event = event_log.log_event(posted_data, event_type_id, user_id, node_id)
                return Response(json.dumps({"success": True, "event_id": new_event.event_id}))
    except APIKeyRateLimited:
        abort(420)
    except APIKeyInvalid:
        abort(404)
    except APIKeySuspended:
        abort(403)


@rest_blueprint.route('/list-event-types/<api_key>', methods=["GET"])
def list_event_types(api_key):
    with current_app.app_context():
        environment = Environment(current_app.config["MYSQL_HOST"],
                                  current_app.config["MYSQL_READ_ONLY_HOST"],
                                  current_app.config["MYSQL_USER"],
                                  current_app.config["MYSQL_PASSWORD"],
                                  current_app.config["MYSQL_DB"],
                                  current_app.config["MYSQL_TEST_DB"],
                                  current_app.config["RATE_LIMIT_QUOTA"],
                                  current_app.config["RATE_LIMIT_RESET"],
                                  current_app.config["REDIS_MASTER_HOST"],
                                  current_app.config["REDIS_READ_ONLY_HOST"])

    db = Database(logger=current_app.logger, env=environment)
    event_log = EventLog(db, logger=current_app.logger)
    try:
        node = event_log.get_api_key_object(api_key)
        event_log.update_quota(node)
        output = json.dumps({"success": True, "event_types": event_log.list_event_types()})
        return output
    except APIKeyRateLimited:
        abort(420)
    except APIKeyInvalid:
        abort(404)
    except APIKeySuspended:
        abort(403)


# Internal rest functions (session_token vs. api_key)


@rest_blueprint.route('/event-type/add/<session_token>', methods=['POST'])
def add_event_type(session_token):
    with current_app.app_context():
        environment = Environment(current_app.config["MYSQL_HOST"],
                                  current_app.config["MYSQL_READ_ONLY_HOST"],
                                  current_app.config["MYSQL_USER"],
                                  current_app.config["MYSQL_PASSWORD"],
                                  current_app.config["MYSQL_DB"],
                                  current_app.config["MYSQL_TEST_DB"],
                                  current_app.config["RATE_LIMIT_QUOTA"],
                                  current_app.config["RATE_LIMIT_RESET"],
                                  current_app.config["REDIS_MASTER_HOST"],
                                  current_app.config["REDIS_READ_ONLY_HOST"])

    db = Database(logger=current_app.logger, env=environment)
    user_object = db.validate_session(session_token)
    if user_object and user_object.has_permission("add-event-type"):
        new_event_type = request.form["new_event_type"]
        if EVENT_TYPE_REGEX.match(new_event_type):
            new_event_type_id = db.create_event_type(new_event_type)
            if new_event_type_id:
                return Response(json.dumps({"new_event_type_id": new_event_type_id,
                                            "success": True}))
            else:
                return Response(json.dumps({"success": False,
                                            "error_message": "Could not add to database.",
                                            "error_code": 1}))
        else:
            return Response(json.dumps({"success": False,
                                        "error_message": "Invalid event type name.",
                                        "error_code": 2}))
    return Response(status=403)
