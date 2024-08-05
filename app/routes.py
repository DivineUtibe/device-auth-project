import os
import qrcode
import uuid
import logging
from datetime import datetime
from pytz import timezone
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, make_response
from .models import Device, SignIn
from . import db

main = Blueprint('main', __name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Generate a unique device ID
def generate_device_id():
    return str(uuid.uuid4())

# Set timezone for Lagos, Nigeria
lagos_tz = timezone('Africa/Lagos')

# Route for home page
@main.route('/')
def home():
    return render_template('home.html')

# Route to check if the device is registered
@main.route('/device_check')
def device_check():
    # Check for device ID in the request args
    device_id = request.args.get('device_id')
    cookie_device_id = request.cookies.get('device_id')
    
    if device_id is None and cookie_device_id is None:
        flash('Invalid device ID.')
        return redirect(url_for('main.home'))

    # Use device_id from the request if present, otherwise use the cookie
    device_id = device_id or cookie_device_id

    # Debugging output
    logging.debug(f"Device ID from request: {device_id}")
    logging.debug(f"Device ID from cookie: {cookie_device_id}")

    # Check if device_id exists
    device = Device.query.filter_by(device_id=device_id).first()
    if device:
        # Set a cookie with the device_id and redirect to sign_in
        response = make_response(redirect(url_for('main.sign_in')))
        response.set_cookie('device_id', device_id, max_age=60*60*24*365*2)  # Cookie valid for 2 years
        return response
    else:
        # Redirect to register with device_id in query string
        response = make_response(redirect(url_for('main.register', device_id=device_id)))
        response.set_cookie('device_id', device_id, max_age=60*60*24*365*2)  # Cookie valid for 2 years
        return response

# Route to register device
@main.route('/register', methods=['GET', 'POST'])
def register():
    device_id = request.args.get('device_id')

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')

        # Check if the email already exists
        existing_device = Device.query.filter_by(email=email).first()
        if existing_device:
            flash('This email is already registered. Please sign in.')
            return redirect(url_for('main.sign_in'))

        # Save the name, email, and device_id to the database
        new_device = Device(name=name, email=email, device_id=device_id)
        db.session.add(new_device)
        db.session.commit()

        # Set a cookie with the device_id and redirect to sign_in
        response = redirect(url_for('main.sign_in'))
        response.set_cookie('device_id', device_id, max_age=60*60*24*365*2)  # Cookie valid for 2 years
        flash('Device registered successfully!')
        return response

    return render_template('register.html', device_id=device_id)

# Route to sign in
@main.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    device_id = request.cookies.get('device_id')
    
    if not device_id:
        flash('Device ID not found. Please scan the QR code again.')
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        name = request.form['name']
        
        # Check if the selected name corresponds to a registered device
        device = Device.query.filter_by(name=name, device_id=device_id).first()
        if device:
            # Use the Lagos timezone
            current_time = datetime.now(lagos_tz)
            sign_in_today = SignIn.query.filter_by(name=name, date=current_time.date()).first()
            
            if sign_in_today:
                flash('You have already signed in for today.')
            else:
                new_sign_in = SignIn(
                    name=name,
                    device_id=device.device_id,
                    date=current_time.date(),
                    time=current_time.time()
                )
                db.session.add(new_sign_in)
                db.session.commit()
                flash('Signed in successfully!')
        else:
            flash('Device not registered. Please register first.')
            return redirect(url_for('main.register', device_id=device_id))

        return redirect(url_for('main.sign_in'))

    devices = Device.query.all()
    return render_template('sign_in.html', devices=devices)

# Route to view sign-in data
@main.route('/sign_in_data')
def sign_in_data():
    # Query the SignIn table, ordering by date and time
    sign_ins = SignIn.query.order_by(SignIn.date.desc(), SignIn.time.desc()).all()
    return render_template('sign_in_data.html', sign_ins=sign_ins)

# Route for backend management page
@main.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if 'delete_device' in request.form:
            device_id = request.form.get('device_id')
            device = Device.query.filter_by(device_id=device_id).first()
            if device:
                db.session.delete(device)
                db.session.commit()
                flash('Device deleted successfully!')
            else:
                flash('Device not found.')
            return redirect(url_for('main.admin'))

    devices = Device.query.all()
    # Query the SignIn table, ordering by date and time
    sign_ins = SignIn.query.order_by(SignIn.date.desc(), SignIn.time.desc()).all()
    return render_template('admin.html', devices=devices, sign_ins=sign_ins)

# Move the generate_qr route to the admin page
@main.route('/admin/generate_qr')
def generate_qr():
    # Generate static QR code pointing to the device_check endpoint
    qr_data = f"{request.host_url}device_check"
    logging.debug(f"Generating QR code with URL: {qr_data}")
    qr = qrcode.make(qr_data)
    
    qr_path = "static/qrcodes/general_qr.png"
    qr.save(os.path.join(current_app.root_path, qr_path))
    
    return render_template('qr_code.html', qr_code=qr_path)

# Route to delete device
@main.route('/delete_device', methods=['POST'])
def delete_device():
    device_id = request.form.get('device_id')
    device = Device.query.filter_by(device_id=device_id).first()
    if device:
        db.session.delete(device)
        db.session.commit()
        flash('Device deleted successfully!')
    else:
        flash('Device not found.')
    return redirect(url_for('main.admin'))
