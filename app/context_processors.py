from .models import Main_Category
from decimal import Decimal

def department_menu(request):
    main_category = Main_Category.objects.prefetch_related(
        'categories__subcategories'
    )

    return {
        'main_category': main_category,
    }


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