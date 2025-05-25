from flask import Blueprint, request, abort, jsonify, session
from rag.rag_morning_eat import order_real_time
from setup import cus_choice, vectorstore, conn

order = Blueprint('ordering', __name__,)


@order.route('/order')
def ordering():
    try:
        data = request.json
        data = data.get('text', '')
        if not data:
            return jsonify({'error': 'No text provided'}), 400
        order_state = session.get('order_state', None)
        response, order_state = order_real_time(data, vectorstore=vectorstore, cus_choice=cus_choice, order_state=order_state, conn=conn)
        session['order_state'] = order_state
        return jsonify({'response': response, 'order_state': order_state})
    except Exception as e:
        print(str(e))
        return jsonify({'error': 'Invalid request format'}), 400