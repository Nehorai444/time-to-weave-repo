from flask import Blueprint, request, jsonify
from models import db, Payment
from auth.token_utils import get_user_id_from_token

payment_bp = Blueprint('payment', __name__, url_prefix='/api/payments')

@payment_bp.route('', methods=['POST'])
def create_payment():
    user_id = get_user_id_from_token(request)
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data or 'amount' not in data:
        return jsonify({"error": "Missing payment amount"}), 400

    try:
        amount = float(data['amount'])
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount value"}), 400

    payment_method = data.get('payment_method', 'manual')
    description = data.get('description', '')

    new_payment = Payment(
        user_id=user_id,
        amount=amount,
        payment_method=payment_method,
        description=description
    )

    try:
        db.session.add(new_payment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify({"message": "Payment recorded", "payment_id": new_payment.id}), 201


@payment_bp.route('', methods=['GET'])
def get_user_payments():
    user_id = get_user_id_from_token(request)
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    payments = Payment.query.filter_by(user_id=user_id).order_by(Payment.created_at.desc()).all()

    result = [{
        'id': p.id,
        'amount': float(p.amount),
        'payment_method': p.payment_method,
        'description': p.description,
        'created_at': p.created_at.isoformat()
    } for p in payments]

    return jsonify(result)
