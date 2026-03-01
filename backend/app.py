from datetime import date, datetime, timedelta
import secrets

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///entitlements_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app)

TOKENS = {}
PASSWORD_HASH_METHOD = 'pbkdf2:sha256'


def hash_password(password: str) -> str:
    return generate_password_hash(password, method=PASSWORD_HASH_METHOD)


class AppUser(db.Model):
    __tablename__ = 'app_users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    role = db.Column(db.String(20), nullable=False, default='developer')
    password_hash = db.Column(db.String(255), nullable=False)


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=True)


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    access_type = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False, default='')


class Entitlement(db.Model):
    __tablename__ = 'entitlements'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    end_date = db.Column(db.Date, nullable=False)
    is_revoked = db.Column(db.Boolean, nullable=False, default=False)
    revoked_at = db.Column(db.DateTime, nullable=True)

    customer = db.relationship('Customer', backref='entitlements')
    product = db.relationship('Product', backref='entitlements')


class PurchaseHistory(db.Model):
    __tablename__ = 'purchase_history'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    date_start = db.Column(db.Date, nullable=False)
    date_end = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    customer = db.relationship('Customer', backref='purchase_history')
    product = db.relationship('Product')


class AccessHistory(db.Model):
    __tablename__ = 'access_history'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    page = db.Column(db.String(200), nullable=False)
    accessed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    customer = db.relationship('Customer', backref='access_history')


def parse_date(value):
    return datetime.strptime(value, '%Y-%m-%d').date()


def calc_end_date(start, length_days):
    return start + timedelta(days=length_days)


def entitlement_to_dict(ent):
    today = date.today()
    is_expired = ent.end_date < today
    is_active = (not ent.is_revoked) and (not is_expired)
    return {
        'id': ent.id,
        'customer': ent.customer_id,
        'customer_email': ent.customer.email,
        'product': ent.product_id,
        'product_name': ent.product.name,
        'start_date': ent.start_date.isoformat(),
        'end_date': ent.end_date.isoformat(),
        'is_revoked': ent.is_revoked,
        'revoked_at': ent.revoked_at.isoformat() if ent.revoked_at else None,
        'is_expired': is_expired,
        'is_active': is_active,
    }


def app_user_to_dict(user):
    return {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role}


def customer_to_dict(customer):
    return {
        'id': customer.id,
        'name': customer.name,
        'email': customer.email,
        'address': customer.address,
    }


def product_to_dict(product):
    return {
        'id': product.id,
        'name': product.name,
        'access_type': product.access_type,
        'description': product.description or '',
    }


def purchase_to_dict(row):
    return {
        'id': row.id,
        'customer': row.customer_id,
        'customer_email': row.customer.email,
        'product': row.product_id,
        'product_name': row.product.name,
        'price': row.price,
        'date_start': row.date_start.isoformat(),
        'date_end': row.date_end.isoformat(),
        'created_at': row.created_at.isoformat(),
    }


def access_to_dict(row):
    return {
        'id': row.id,
        'customer': row.customer_id,
        'customer_email': row.customer.email,
        'page': row.page,
        'accessed_at': row.accessed_at.isoformat(),
    }


def current_user():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.replace('Bearer ', '', 1).strip()
    user_id = TOKENS.get(token)
    if not user_id:
        return None
    return AppUser.query.get(user_id)


def require_auth():
    user = current_user()
    if not user:
        return None, (jsonify({'error': 'Authentication required'}), 401)
    return user, None


def require_support():
    user, error = require_auth()
    if error:
        return None, error
    if user.role != 'support':
        return None, (jsonify({'error': 'Support role required'}), 403)
    return user, None


@app.post('/api/auth/login')
def login():
    payload = request.get_json(force=True)
    email = payload.get('email', '').strip().lower()
    password = payload.get('password', '')

    user = AppUser.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = secrets.token_hex(24)
    TOKENS[token] = user.id
    return jsonify({'token': token, 'role': user.role, 'user_id': user.id})


@app.get('/api/app-users')
def list_app_users():
    user, error = require_auth()
    if error:
        return error
    del user
    rows = AppUser.query.order_by(AppUser.id).all()
    return jsonify([app_user_to_dict(row) for row in rows])


@app.get('/api/customers')
def list_customers():
    user, error = require_auth()
    if error:
        return error
    del user
    rows = Customer.query.order_by(Customer.id).all()
    return jsonify([customer_to_dict(row) for row in rows])


@app.get('/api/products')
def list_products():
    user, error = require_auth()
    if error:
        return error
    del user
    return jsonify([product_to_dict(row) for row in Product.query.order_by(Product.id).all()])




@app.put('/api/products/<int:product_id>')
def update_product(product_id):
    user, error = require_support()
    if error:
        return error
    del user

    product = Product.query.get_or_404(product_id)
    payload = request.get_json(force=True)

    name = payload.get('name', '').strip()
    access_type = payload.get('access_type', '').strip().lower()
    description = payload.get('description', '').strip()

    if not name:
        return jsonify({'error': 'name is required'}), 400
    if access_type not in {'digital', 'print', 'premium'}:
        return jsonify({'error': 'access_type must be one of: digital, print, premium'}), 400

    existing = Product.query.filter(Product.id != product.id, Product.name == name).first()
    if existing:
        return jsonify({'error': 'product name already exists'}), 400

    product.name = name
    product.access_type = access_type
    product.description = description
    db.session.commit()
    return jsonify(product_to_dict(product))


@app.get('/api/entitlements')
def list_entitlements():
    user, error = require_auth()
    if error:
        return error
    del user
    rows = Entitlement.query.order_by(Entitlement.id.desc()).all()
    return jsonify([entitlement_to_dict(row) for row in rows])


@app.post('/api/entitlements')
def create_entitlement():
    user, error = require_support()
    if error:
        return error
    del user
    payload = request.get_json(force=True)

    start_date = parse_date(payload.get('start_date'))
    length_days = int(payload.get('length_days', 0))
    if length_days < 1:
        return jsonify({'error': 'length_days must be >= 1'}), 400

    entitlement = Entitlement(
        customer_id=int(payload['customer']),
        product_id=int(payload['product']),
        start_date=start_date,
        end_date=calc_end_date(start_date, length_days),
    )
    db.session.add(entitlement)
    db.session.flush()

    purchase = PurchaseHistory(
        customer_id=entitlement.customer_id,
        product_id=entitlement.product_id,
        price=float(payload.get('price', 9.99)),
        date_start=entitlement.start_date,
        date_end=entitlement.end_date,
    )
    db.session.add(purchase)
    db.session.commit()
    return jsonify(entitlement_to_dict(entitlement)), 201


@app.put('/api/entitlements/<int:entitlement_id>')
def update_entitlement(entitlement_id):
    user, error = require_support()
    if error:
        return error
    del user
    ent = Entitlement.query.get_or_404(entitlement_id)
    payload = request.get_json(force=True)

    if 'customer' in payload:
        ent.customer_id = int(payload['customer'])
    if 'product' in payload:
        ent.product_id = int(payload['product'])
    if 'start_date' in payload:
        ent.start_date = parse_date(payload['start_date'])
    if 'length_days' in payload:
        ent.end_date = calc_end_date(ent.start_date, int(payload['length_days']))

    db.session.commit()
    return jsonify(entitlement_to_dict(ent))


@app.post('/api/entitlements/<int:entitlement_id>/revoke')
def revoke_entitlement(entitlement_id):
    user, error = require_support()
    if error:
        return error
    del user
    ent = Entitlement.query.get_or_404(entitlement_id)
    ent.is_revoked = True
    ent.revoked_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'status': 'revoked'})


@app.get('/api/customers/<int:customer_id>/rights')
def customer_rights(customer_id):
    user, error = require_auth()
    if error:
        return error
    del user

    customer = Customer.query.get_or_404(customer_id)
    today = date.today()
    rows = Entitlement.query.filter(
        Entitlement.customer_id == customer_id,
        Entitlement.is_revoked.is_(False),
        Entitlement.end_date >= today,
    ).order_by(Entitlement.id.desc()).all()

    log = AccessHistory(customer_id=customer.id, page=f'/customers/{customer_id}/rights')
    db.session.add(log)
    db.session.commit()

    return jsonify({'customer': customer_to_dict(customer), 'active_rights': [entitlement_to_dict(row) for row in rows]})


@app.get('/api/purchase-history')
def purchase_history():
    user, error = require_auth()
    if error:
        return error
    del user
    rows = PurchaseHistory.query.order_by(PurchaseHistory.created_at.desc()).all()
    return jsonify([purchase_to_dict(row) for row in rows])


@app.get('/api/access-history')
def access_history():
    user, error = require_auth()
    if error:
        return error
    del user
    rows = AccessHistory.query.order_by(AccessHistory.accessed_at.desc()).all()
    return jsonify([access_to_dict(row) for row in rows])



def ensure_schema_updates():
    inspector = inspect(db.engine)
    product_columns = {column['name'] for column in inspector.get_columns('products')}
    if 'description' not in product_columns:
        db.session.execute(text("ALTER TABLE products ADD COLUMN description TEXT NOT NULL DEFAULT ''"))
        db.session.commit()

def seed_data():
    products = [
        ('Digital Basic', 'digital', 'Digital-only online reading access for daily articles.'),
        ('Print Weekly', 'print', 'Weekly physical paper delivery with core sections.'),
        ('Premium All-Access', 'premium', 'Digital + print bundle with premium investigative content.'),
    ]
    for name, access_type, description in products:
        existing_product = Product.query.filter_by(name=name).first()
        if not existing_product:
            db.session.add(Product(name=name, access_type=access_type, description=description))
        elif not existing_product.description:
            existing_product.description = description

    # app users (operators, not entitlement customers)
    if not AppUser.query.filter_by(email='support@example.com').first():
        db.session.add(
            AppUser(
                name='Support Agent',
                email='support@example.com',
                role='support',
                password_hash=hash_password('Support123!'),
            )
        )

    if not AppUser.query.filter_by(email='developer@example.com').first():
        db.session.add(
            AppUser(
                name='Dev Reader',
                email='developer@example.com',
                role='developer',
                password_hash=hash_password('Developer123!'),
            )
        )

    # customers (media consumers)
    customers = [
        ('Alex Reader', 'alex.reader@example.com', '101 Main St'),
        ('Priya Subscriber', 'priya.subscriber@example.com', '22 Ocean Ave'),
        ('Morgan Print', 'morgan.print@example.com', '77 Pine Rd'),
    ]
    for name, email, address in customers:
        if not Customer.query.filter_by(email=email).first():
            db.session.add(Customer(name=name, email=email, address=address))

    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        ensure_schema_updates()
        seed_data()
    app.run(host='0.0.0.0', port=8000, debug=True)
