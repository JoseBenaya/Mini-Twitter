from flask import Flask
from flask_sqlalchemy import SQLAlchemy

#Presentation Layer

app = Flask(__name__)
app.secret_key = "Sangat Rahasia"

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/uts'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


from routes import *

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
