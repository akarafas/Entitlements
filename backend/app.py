from datetime import date, datetime, timedelta
import secrets

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///entitlements.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app)

TOKENS = {}


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='developer')
    password_hash = db.Column(db.String(255), nullable=False)


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    access_type = db.Column(db.String(20), nullable=False)


class Entitlement(db.Model):
    __tablename__ = 'entitlements'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    end_date = db.Column(db.Date, nullable=False)
    is_revoked = db.Column(db.Boolean, nullable=False, default=False)
    revoked_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='entitlements')
    product = db.relationship('Product', backref='entitlements')


class PurchaseHistory(db.Model):
    __tablename__ = 'purchase_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    date_start = db.Column(db.Date, nullable=False)
    date_end = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='purchase_history')
    product = db.relationship('Product')


class AccessHistory(db.Model):
    __tablename__ = 'access_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    page = db.Column(db.String(200), nullable=False)
    accessed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='access_history')


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
        'user': ent.user_id,
        'user_email': ent.user.email,
        'product': ent.product_id,
        'product_name': ent.product.name,
        'start_date': ent.start_date.isoformat(),
        'end_date': ent.end_date.isoformat(),
        'is_revoked': ent.is_revoked,
        'revoked_at': ent.revoked_at.isoformat() if ent.revoked_at else None,
        'is_expired': is_expired,
        'is_active': is_active,
    }


def product_to_dict(product):
    return {'id': product.id, 'name': product.name, 'access_type': product.access_type}


def user_to_dict(user):
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'address': user.address,
        'role': user.role,
    }


def purchase_to_dict(row):
    return {
        'id': row.id,
        'user': row.user_id,
        'user_email': row.user.email,
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
        'user': row.user_id,
        'user_email': row.user.email,
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
    return User.query.get(user_id)


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

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = secrets.token_hex(24)
    TOKENS[token] = user.id
    return jsonify({'token': token, 'role': user.role, 'user_id': user.id})


@app.get('/api/users')
def list_users():
    user, error = require_auth()
    if error:
        return error
    del user
    return jsonify([user_to_dict(row) for row in User.query.order_by(User.id).all()])


@app.get('/api/products')
def list_products():
    user, error = require_auth()
    if error:
        return error
    del user
    return jsonify([product_to_dict(row) for row in Product.query.order_by(Product.id).all()])


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
        user_id=int(payload['user']),
        product_id=int(payload['product']),
        start_date=start_date,
        end_date=calc_end_date(start_date, length_days),
    )
    db.session.add(entitlement)
    db.session.flush()

    purchase = PurchaseHistory(
        user_id=entitlement.user_id,
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

    if 'user' in payload:
        ent.user_id = int(payload['user'])
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


@app.get('/api/users/<int:user_id>/rights')
def user_rights(user_id):
    request_user, error = require_auth()
    if error:
        return error

    target_user = User.query.get_or_404(user_id)
    today = date.today()
    rows = Entitlement.query.filter(
        Entitlement.user_id == user_id,
        Entitlement.is_revoked.is_(False),
        Entitlement.end_date >= today,
    ).order_by(Entitlement.id.desc()).all()

    log = AccessHistory(user_id=request_user.id, page=f'/users/{user_id}/rights')
    db.session.add(log)
    db.session.commit()

    return jsonify({'user': user_to_dict(target_user), 'active_rights': [entitlement_to_dict(row) for row in rows]})


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


def seed_data():
    products = [
        ('Digital Basic', 'digital'),
        ('Print Weekly', 'print'),
        ('Premium All-Access', 'premium'),
    ]
    for name, access_type in products:
        existing = Product.query.filter_by(name=name).first()
        if not existing:
            db.session.add(Product(name=name, access_type=access_type))

    support = User.query.filter_by(email='support@example.com').first()
    if not support:
        db.session.add(
            User(
                name='Support Agent',
                email='support@example.com',
                address='123 Support Street',
                role='support',
                password_hash=generate_password_hash('Support123!', method='pbkdf2:sha256'),
            )
        )

    developer = User.query.filter_by(email='developer@example.com').first()
    if not developer:
        db.session.add(
            User(
                name='Dev Reader',
                email='developer@example.com',
                address='456 Developer Avenue',
                role='developer',
                password_hash=generate_password_hash('Developer123!', method='pbkdf2:sha256'),
            )
        )
    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(host='0.0.0.0', port=8000, debug=True)
