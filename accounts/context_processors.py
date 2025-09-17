from messaging.models import Message, Conversation


def message_notifications(request):
    """Context processor to provide real message notifications"""
    if request.user.is_authenticated:
        # Count unread messages for the current user
        unread_count = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
        
        # Count pending orders for sellers
        pending_orders_count = 0
        favorites_count = 0
        if request.user.is_seller:
            from dogs.models import Order
            pending_orders_count = Order.objects.filter(
                dog__seller=request.user,
                status='pending'
            ).count()
        else:
            # Buyers: count total favorites across dogs and accessories
            try:
                from dogs.models import Favorite as DogFavorite
                from accessories.models import AccessoryFavorite
                favorites_count = (
                    DogFavorite.objects.filter(user=request.user).count()
                    + AccessoryFavorite.objects.filter(user=request.user).count()
                )
            except Exception:
                favorites_count = 0
        
        return {
            'unread_messages_count': unread_count,
            'pending_orders_count': pending_orders_count,
            'favorites_count': favorites_count,
        }
    
    return {
        'unread_messages_count': 0,
        'pending_orders_count': 0,
        'favorites_count': 0,
    }
