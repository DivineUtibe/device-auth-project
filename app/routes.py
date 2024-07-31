from flask import Blueprint, request, render_template, redirect, url_for, flash
import qrcode
import uuid
from .models import Device
from . import db

main = Blueprint('main', __name__)

# Generate a unique device ID
def generate_device_id():
    return str(uuid.uuid4())

# Route to display the general QR code
@main.route('/qr_code')
def qr_code():
    # Generate the general QR code URL
    qr_data = "http://127.0.0.1:5000/register"
    qr = qrcode.make(qr_data)
    qr.save("app/static/qrcodes/general_qr.png")
    return render_template('qr_code.html', qr_code="static/qrcodes/general_qr.png")

# Route to register device
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        device_id = generate_device_id()

        try:
            # Save the email and device_id to the database
            new_device = Device(email=email, device_id=device_id)
            db.session.add(new_device)
            db.session.commit()
            flash('Device registered successfully!')
        except Exception as e:
            db.session.rollback()  # Rollback the transaction on error
            flash(f'Error registering device: {e}')
        
        return redirect(url_for('main.register'))

    return render_template('register.html')

# Route to authenticate device
@main.route('/authenticate', methods=['GET', 'POST'])
def authenticate():
    if request.method == 'POST':
        email = request.form['email']
        device_id = request.form['device_id']

        try:
            # Check the email and device_id against the database
            device = Device.query.filter_by(email=email, device_id=device_id).first()
            if device:
                flash('Device authenticated successfully!')
            else:
                flash('Authentication failed.')
        except Exception as e:
            flash(f'Error during authentication: {e}')

        return redirect(url_for('main.authenticate'))

    return render_template('authenticate.html')

# Default route for home
@main.route('/')
def home():
    return "Home Page - QR Code Authentication System"
