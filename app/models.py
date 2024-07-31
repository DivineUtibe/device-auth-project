from . import db

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    device_id = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<Device {self.email}>'
