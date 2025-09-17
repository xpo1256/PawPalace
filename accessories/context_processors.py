def cart_count(request):
    cart = request.session.get('cart', {})
    try:
        # Unified cart structure: {'accessories': {id: qty}, 'dogs': {id: 1}}
        acc = cart.get('accessories', {}) if isinstance(cart, dict) else {}
        dogs = cart.get('dogs', {}) if isinstance(cart, dict) else {}
        count = sum(int(qty) for qty in acc.values()) + len(dogs.keys())
        return {'cart_count': count}
    except Exception:
        return {'cart_count': 0}


