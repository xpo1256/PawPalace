def cart_count(request):
    cart = request.session.get('cart', {})
    try:
        return {'cart_count': sum(int(qty) for qty in cart.values())}
    except Exception:
        return {'cart_count': 0}


