from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.conf import settings
import razorpay

from .models import Cart, Customer, Item, Restaurant

def say_hello(request):
    return render(request, "index.html")

def open_signup(request):
    return render(request, "signup.html")

def open_signin(request):
    return render(request, "signin.html")

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')
        try:
            Customer.objects.get(username = username)
            return HttpResponse("Duplicate username!")
        except:
            Customer.objects.create(
                username = username,
                password = password,
                email = email,
                mobile = mobile,
                address = address,
            )
            request.session['username'] = username
            return redirect('customer_home')
    return render(request, 'signin.html')

def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            Customer.objects.get(username=username, password=password)
            request.session['username'] = username
            if username == 'admin':
                return redirect('admin_home')
            else:
                return redirect('customer_home')
        except Customer.DoesNotExist:
            return render(request, 'fail.html')
    return render(request, 'signin.html')

def logout_view(request):
    request.session.flush()
    return redirect('say_hello')

def admin_home(request):
    if request.session.get('username') != 'admin':
        return redirect('open_signin')
    return render(request, 'admin_home.html')

def customer_home(request):
    username = request.session.get('username')
    if not username:
        return redirect('open_signin')
    restaurantList = Restaurant.objects.all()
    return render(request, 'customer_home.html', {"restaurantList" : restaurantList})

def open_add_restaurant(request):
    if request.session.get('username') != 'admin': return redirect('open_signin')
    return render(request, 'add_restaurant.html')

def add_restaurant(request):
    if request.session.get('username') != 'admin': return redirect('open_signin')
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')
        try:
            Restaurant.objects.get(name = name)
            return HttpResponse("Duplicate restaurant!")
        except:
            Restaurant.objects.create(name=name, picture=picture, cuisine=cuisine, rating=rating)
            return redirect('open_show_restaurant')
    return redirect('admin_home')

def open_show_restaurant(request):
    if request.session.get('username') != 'admin': return redirect('open_signin')
    restaurantList = Restaurant.objects.all()
    return render(request, 'show_restaurant.html',{"restaurantList" : restaurantList})

def open_update_restaurant(request, restaurant_id):
    if request.session.get('username') != 'admin': return redirect('open_signin')
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    return render(request, 'update_restaurant.html', {"restaurant" : restaurant})

def update_restaurant(request, restaurant_id):
    if request.session.get('username') != 'admin': return redirect('open_signin')
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    if request.method == 'POST':
        restaurant.name = request.POST.get('name')
        restaurant.picture = request.POST.get('picture')
        restaurant.cuisine = request.POST.get('cuisine')
        restaurant.rating = request.POST.get('rating')
        restaurant.save()
    return redirect('open_show_restaurant')

def delete_restaurant(request, restaurant_id):
    if request.session.get('username') != 'admin': return redirect('open_signin')
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    restaurant.delete()
    return redirect('open_show_restaurant')

def open_update_menu(request, restaurant_id):
    if request.session.get('username') != 'admin': return redirect('open_signin')
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    itemList = restaurant.items.all()
    return render(request, 'update_menu.html', {"itemList" : itemList, "restaurant" : restaurant})

def update_menu(request, restaurant_id):
    if request.session.get('username') != 'admin': return redirect('open_signin')
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        vegeterian = request.POST.get('vegeterian') == 'on'
        picture = request.POST.get('picture')
        try:
            Item.objects.get(name = name)
            return HttpResponse("Duplicate item!")
        except:
            Item.objects.create(
                restaurant = restaurant,
                name = name,
                description = description,
                price = price,
                vegeterian = vegeterian,
                picture = picture,
            )
    return redirect('open_update_menu', restaurant_id=restaurant_id)

def view_menu(request, restaurant_id):
    username = request.session.get('username')
    if not username: return redirect('open_signin')
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    itemList = restaurant.items.all()
    return render(request, 'customer_menu.html', {"itemList" : itemList, "restaurant" : restaurant})

def add_to_cart(request, item_id):
    username = request.session.get('username')
    if not username: return redirect('open_signin')
    item = get_object_or_404(Item, id=item_id)
    customer = get_object_or_404(Customer, username=username)
    cart, created = Cart.objects.get_or_create(customer=customer)
    cart.items.add(item)
    return redirect('show_cart')

def show_cart(request):
    username = request.session.get('username')
    if not username: return redirect('open_signin')
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0
    return render(request, 'cart.html', {"itemList" : items, "total_price" : total_price})

def checkout(request):
    username = request.session.get('username')
    if not username: return redirect('open_signin')
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    cart_items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    if total_price == 0:
        return render(request, 'checkout.html', {'error': 'Your cart is empty!'})

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    order_data = {'amount': int(total_price * 100), 'currency': 'INR', 'payment_capture': '1'}
    order = client.order.create(data=order_data)

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'order_id': order['id'],
        'amount': total_price,
    })

def orders(request):
    username = request.session.get('username')
    if not username: return redirect('open_signin')
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    cart_items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    if cart:
        cart.items.clear()

    return render(request, 'orders.html', {
        'customer': customer,
        'cart_items': cart_items,
        'total_price': total_price,
    })