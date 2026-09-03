from cart.cart import Cart
from django.http.response import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.db.models import Avg, Max, Min, Sum, Model

from app.models import Slider, banner_area, Main_Category,Product, Category, Color, Brand, Coupon_Code
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from cart.cart import Cart

def BASE(request):
    return render(request, 'base.html')


def HOME(request):
    sliders = Slider.objects.all().order_by('-id')[0:3]
    banners = banner_area.objects.all().order_by('-id')[0:3]

    main_category = Main_Category.objects.all().order_by('-id')
    product = Product.objects.filter(section__name = "Top Deals Of The Day")


    return render(request, 'main/home.html', {
        'sliders': sliders,
        'banners': banners,
        'main_category': main_category,
        'product': product
    })

def ABOUT(request):
    return render(request, 'Main/about.html')

def CONTACT(request):
    return render(request, 'Main/contact.html')

def PRODUCT(request):
    category = Category.objects.all()
    product = Product.objects.all()
    color = Color.objects.all()
    brand = Brand.objects.all()

    min_price = Product.objects.all().aggregate(Min('price'))
    max_price = Product.objects.all().aggregate(Max('price'))
    ColorID = request.GET.get('colorID')

    FilterPrice = request.GET.get('FilterPrice')
    if FilterPrice:
        Int_FilterPrice = int(FilterPrice)
        product = Product.objects.filter(price__lte=Int_FilterPrice)
    elif ColorID:
        product = Product.objects.filter(color=ColorID)
    else:
        product = Product.objects.all()


    return render(request, 'product/product.html',{
        'category': category,
        'product': product,
        'min_price': min_price,
        'max_price': max_price,
        'FilterPrice': FilterPrice,
        'color': color,
        'brand': brand,
    })


def FILTER_DATA(request):
    categories = request.GET.getlist('category') or request.GET.getlist('category[]')
    brands = request.GET.getlist('brand') or request.GET.getlist('brand[]')

    products = Product.objects.all().distinct()

    if categories:
        products = products.filter(Categories__id__in=categories)

    if brands:
        # Assuming your Product model field is named 'brand' or 'Brand'
        products = products.filter(Brand__id__in=brands)

    product_data = list(products.values('id', 'product_name', 'price', 'featured_image'))

    return JsonResponse({'data': product_data})

def PRODUCT_DETAILS(request, slug):
    product = Product.objects.filter(slug=slug).first()

    if product is None:
        return redirect('404')

    return render(request, 'Product/product_detail.html', {
        'product': product
})

def Error404(request):
    return render(request, 'errors/404.html')


def MY_ACCOUNT(request):
    return render(request, 'account/my_account.html')

def REGISTER(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('login')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('login')

        user = User(
            username=username,
            email=email,
        )
        user.set_password(password)
        user.save()
        return redirect('login')


def LOGIN(request):
    if request.method == 'POST':
        username =  request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username or password is incorrect')
            return redirect('login')

@login_required(login_url='/accounts/login/')
def PROFILE(request):
    return render(request, 'profile/profile.html')

@login_required(login_url='/accounts/login/')
def UPDATE_PROFILE(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        user_id = request.user.id

        user =  User.objects.get(id=user_id)
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.email = email

        if password != None and password != "":
            user.set_password(password)
        user.save()
        messages.success(request, 'Profile updated successfully')

        return redirect('handleprofile')



@login_required(login_url='/accounts/login/')
def cart_add(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.add(product=product)
    return redirect('cart_detail')

@login_required(login_url='/accounts/login/')
def item_clear(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.remove(product)
    return redirect('cart_detail')

@login_required(login_url='/accounts/login/')
def item_increment(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.add(product=product)
    return redirect('cart_detail')

@login_required(login_url='/accounts/login/')
def item_decrement(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.decrement(product=product)
    return redirect('cart_detail')

@login_required(login_url='/accounts/login/')
def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    return redirect('cart_detail')

@login_required(login_url='/accounts/login/')
def cart_detail(request):
    cart = request.session.get('cart', {})
    packing_cost = sum(float(i.get('packing_cost', 0)) for i in cart.values() if i)
    tax = sum(float(i.get('tax', 0)) for i in cart.values() if i)

    coupon = None
    valid_coupon = None
    invalid_coupon = None

    if request.method == 'GET':
        coupon_code = request.GET.get('coupon_code')
        if coupon_code:
            try:
                coupon = Coupon_Code.objects.get(code=coupon_code)
                valid_coupon = "Are applicable on current order!"

                # SAVE COUPON TO SESSION SO CHECKOUT CAN ACCESS IT
                request.session['coupon_code'] = coupon.code
                # Change 'discount' to whatever your model field name is (e.g., coupon.discount or coupon.percentage)
                request.session['coupon_discount_percent'] = float(coupon.discount)

            except Coupon_Code.DoesNotExist:
                invalid_coupon = "Invalid Coupon Code !"
                # Clear session coupon if invalid code is tried
                request.session.pop('coupon_code', None)
                request.session.pop('coupon_discount_percent', None)

    return render(request, 'cart/cart.html', {
        'cart': cart,
        'packing_cost': packing_cost,
        'tax': tax,
        'coupon': coupon,
        'valid_coupon': valid_coupon,
        'invalid_coupon': invalid_coupon,
    })
def CHECKOUT(request):
    cart = request.session.get('cart', {})

    # Calculate subtotal, packing, and tax dynamically
    cart_subtotal = sum(float(item['price']) * int(item['quantity']) for item in cart.values() if item)
    packing_cost = sum(float(item.get('packing_cost', 0)) for item in cart.values() if item)
    tax = sum(float(item.get('tax', 0)) for item in cart.values() if item)
    tax_and_packing_cost = packing_cost + tax

    # Retrieve discount percent stored in session from cart page (matches the key saved in cart_detail)
    discount_percent = float(request.session.get('coupon_discount_percent', 0))
    print("Discount Percent:", discount_percent)

    # Fallback if posted directly
    if request.method == 'POST' and request.POST.get('coupon_discount'):
        discount_percent = float(request.POST.get('coupon_discount', 0))

    # Calculate actual coupon discount value in Rupees
    coupon_discount = (cart_subtotal * discount_percent) / 100 if discount_percent else 0.0

    # Grand Total Calculation
    order_total = (cart_subtotal + tax_and_packing_cost) - coupon_discount

    context = {
        'cart': cart,
        'cart_subtotal': cart_subtotal,
        'tax_and_packing_cost': tax_and_packing_cost,
        'discount_percent': discount_percent,
        'coupon_discount': coupon_discount,
        'order_total': order_total,
    }

    return render(request, 'checkout/checkout.html', context)