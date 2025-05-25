from flask import Blueprint, request, abort, jsonify, session
from setup import init_order_state
import uuid

auth = Blueprint('auth', __name__)

@auth.route('/validate', methods=['GET'])
def validate():
    """Validate the session."""
    if 'ordering_system_session' in session:
        return jsonify({'valid': True})
    session['ordering_system_session'] = str(uuid.uuid4())
    session['order_state'] = init_order_state()
    return jsonify({"ok": True})

@auth.route('/reset', methods=['POST'])
def reset():
    """Reset the session."""
    session.clear()
    session['ordering_system_session'] = str(uuid.uuid4())
    session['order_state'] = init_order_state()
    return jsonify({'ok': True, 'ordering_system_session': session['ordering_system_session']})

@auth.route('/get_order_state', methods=['GET'])
def get_order_state():
    """Get the current order state."""
    order_state = session.get('order_state', None)
    if not order_state:
        return jsonify({'error': 'No order state found'}), 404
    return jsonify(order_state)

@auth.route('/set_order_state', methods=['POST'])
def set_order_state():
    """Set the current order state."""
    data = request.json
    if not data or 'order_state' not in data:
        return jsonify({'error': 'Invalid request format'}), 400
    session['order_state'] = data['order_state']
    return jsonify({'ok': True, 'order_state': session['order_state']})

@auth.route('/clear_order_state', methods=['POST'])
def clear_order_state():
    """Clear the current order state."""
    session.pop('order_state', None)
    return jsonify({'ok': True, 'order_state': None})
