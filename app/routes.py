from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, make_response
import os
import qrcode
import uuid
from datetime import datetime
from .models import Device, SignIn
from . import db

main = Blueprint('main', __name__)

# Generate a unique device ID
def generate_device_id():
    return str(uuid.uuid4())

# Route for home page
@main.route('/')
def home():
    return render_template('home.html')

# Route to display the general QR code
@main.route('/generate_qr')
def generate_qr():
    # Generate a unique device ID for the QR code
    device_id = generate_device_id()
    qr_data = f"{request.host_url}device_check?device_id={device_id}"
    qr = qrcode.make(qr_data)
    
    qr_path = "static/qrcodes/general_qr.png"
    qr.save(os.path.join(current_app.root_path, qr_path))
    
    return render_template('qr_code.html', qr_code=qr_path)

# Route to check if the device is registered
@main.route('/device_check')
def device_check():
    device_id = request.args.get('device_id')
    cookie_device_id = request.cookies.get('device_id')
    
    if not device_id and not cookie_device_id:
        flash('Invalid device ID.')
        return redirect(url_for('main.home'))
    
    if not device_id:
        device_id = cookie_device_id

    # Debugging output
    print(f"Device ID from request: {device_id}")
    print(f"Device ID from cookie: {cookie_device_id}")

    # Check if device_id exists
    device = Device.query.filter_by(device_id=device_id).first()
    if device:
        # Set a cookie with the device_id and redirect to sign_in
        response = make_response(redirect(url_for('main.sign_in')))
        response.set_cookie('device_id', device_id, max_age=60*60*24*365*2)  # Cookie valid for 2 years
        return response
    else:
        # Redirect to register with device_id in query string
        return redirect(url_for('main.register', device_id=device_id))

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
            new_sign_in = SignIn(name=name, device_id=device.device_id)
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
    sign_ins = SignIn.query.order_by(SignIn.date.desc(), SignIn.time.desc()).all()
    return render_template('admin.html', devices=devices, sign_ins=sign_ins)

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
