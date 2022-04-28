from app import db
import datetime

# Data Access Layer
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True)
    join_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    messages = db.relationship('Message', backref='messages', lazy='dynamic')
    from_user_id = db.relationship(
        'Relationship', foreign_keys="Relationship.from_user", backref='relationship', lazy='dynamic')
    to_user_id = db.relationship(
        'Relationship', foreign_keys="Relationship.to_user", backref='related_to', lazy='dynamic')

    def following(self):
        return db.session.query(User).join(Relationship, User.id == Relationship.to_user).filter(Relationship.from_user == self.id).order_by(User.username).all()

    def followers(self):
        return db.session.query(User).join(Relationship, User.id == Relationship.from_user).filter(Relationship.to_user == self.id).order_by(User.username).all()

    def is_following(self, user):
        exist = Relationship.query.filter(
            Relationship.from_user == self.id, Relationship.to_user == user.id).first()
        return exist


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(100))
    published_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Relationship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)