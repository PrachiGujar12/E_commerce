from decimal import Decimal


def cart_processor(request):
    cart = request.session.get('cart', {})

    total_amount = sum(
        Decimal(str(item['price'])) * item['quantity']
        for item in cart.values()
    )

    return {
        'cart': cart,
        'cart_total_amount': total_amount,
    }