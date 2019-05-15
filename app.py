from flask import Flask
import admin
import rest

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('development.cfg', silent=False)
app.register_blueprint(admin.admin_blueprint)
app.register_blueprint(rest.rest_blueprint)


@app.route('/')
def homepage():
    return admin.admin_no_session()


if __name__ == '__main__':
    app.run()
