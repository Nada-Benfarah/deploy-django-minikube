from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from .models import Cart, Customer, Product
from .forms import CustomerRegisterationForm, CustomerProfileForm
from django.contrib import messages
from django.db.models import Q
from django.db.models import Sum, F
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

# Set the domain for redirection
YOUR_DOMAIN = 'http://localhost:8000'

# Create your views here.

def home(request):
    return render(request, 'app/home.html')

def about(request):
    return render(request, 'app/about.html')

def contact(request):
    return render(request, 'app/contact.html')


class CategoryView(View):
    def get(self,request,val):
        product = Product.objects.filter(category=val)
        title = Product.objects.filter(category=val).values('title') 
        return render(request, 'app/category.html',locals()) 
    
class CategoryTitle(View):
    def get(self,request,val):
        product = Product.objects.filter(title=val)
        title = Product.objects.filter(category=product[0].category).values('title') 
        return render(request, 'app/category.html',locals()) 
    
class Productdetail(View):
    def get(self,request,pk):
        product = Product.objects.get(pk=pk)
        return render(request, 'app/productdetail.html',locals())
    

class CustomerRegisterationView(View):
    def get(self,request):
        form = CustomerRegisterationForm()
        return render(request, 'app/customerregistration.html',locals()) 
    def post(self,request):
        form = CustomerRegisterationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Congratulations! User Register Successfully")
        else:
            messages.warning(request,"Invalid Input Data")
        return render(request, 'app/customerregistration.html',locals()) 
    
class ProfileView(View):
    def get(self,request):
        form = CustomerProfileForm()
        return render(request, 'app/profile.html',locals()) 
    def post(self,request):
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            user = request.user
            name = form.cleaned_data['name']
            locality = form.cleaned_data['locality']
            city = form.cleaned_data['city']
            mobile = form.cleaned_data['mobile']
            state = form.cleaned_data['state']
            zipcode = form.cleaned_data['zipcode']
            reg = Customer(user=user,name=name,locality=locality,mobile=mobile,city=city,state=state,zipcode=zipcode)
            reg.save()
            messages.success(request,"Congratulations! Profile Save Successfully")
        else:
            messages.warning(request,"Invalid Input Data")
        return render(request, 'app/profile.html',locals()) 


def address (request):
    add = Customer.objects.filter(user=request.user)
    return render(request, 'app/address.html',locals())

class updateAddress(View):
    def get(self,request,pk):
        add = Customer.objects.get(pk=pk)
        form = CustomerProfileForm(instance=add)
        return render(request, 'app/updateaddress.html',locals()) 
    def post(self,request,pk):
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            add= Customer.objects.get(pk=pk)
            add.name = form.cleaned_data['name']
            add.locality = form.cleaned_data['locality']
            add.city = form.cleaned_data['city']
            add.mobile = form.cleaned_data['mobile']
            add.state = form.cleaned_data['state']
            add.zipcode = form.cleaned_data['zipcode']
            add.save()
            messages.success(request,"Congratulations! Address Update Successfully")
        else:
            messages.warning(request,"Invalid Input Data")
        return redirect("address")
    
def add_to_cart(request):
    user = request.user
    product_id = request.GET.get('prod_id')
    product = Product.objects.get(id=product_id)

    cart_item, created = Cart.objects.get_or_create(user=user, product=product)
    
    if not created:
        cart_item.quantity = cart_item.quantity + 1
        cart_item.save()
        cart_item.refresh_from_db() 
    
    return redirect("/cart")



def show_cart(request):
    user = request.user
    cart = Cart.objects.filter(user=user)
    amount = 0.0
    for p in cart:
        value = (p.quantity * p.product.discounted_price)
        amount += value
    totalamount = amount + 40
    return render(request, 'app/addtocart.html',locals())


def create_checkout_session(request):
    if request.method == "POST":
        user = request.user
        cart_items = Cart.objects.filter(user=user)
        
        if not cart_items:
            return JsonResponse({'error': 'Cart is empty'}, status=400)

        line_items = []
        total_amount = 0

        for item in cart_items:
            product = item.product
            quantity = item.quantity
            unit_price = product.discounted_price
            total_product_price = unit_price * quantity

            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product.title,
                    },
                    'unit_amount': int(unit_price * 100),
                },
                'quantity': quantity,
            })
            total_amount += total_product_price

        shipping_fee = 40
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'Shipping Fee',
                },
                'unit_amount': int(shipping_fee * 100),
            },
            'quantity': 1,
        })
        total_amount += shipping_fee

        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=line_items,
                mode='payment',
                success_url='http://localhost:8000/',
                cancel_url='http://localhost:8000/cancel/',
            )
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

        return redirect(checkout_session.url, code=303)

    return redirect('cart')


def success(request):
    return render(request, 'success.html')

def cancel(request):
    return render(request, 'cancel.html')


class checkout(View):
    def get(self,request):
        user = request.user
        add= Customer.objects.filter(user=user)
        cart_items = Cart.objects.filter(user=user)
        famount = 0.0
        for p in cart_items:
            value = (p.quantity * p.product.discounted_price)
            famount = famount + value
        totalamount = famount + 40
        return render(request, 'app/checkout.html',locals())



def plus_cart(request):
    user = request.user
    product_id = request.GET.get('prod_id')
    product = Product.objects.get(id=product_id)

    cart_item, created = Cart.objects.get_or_create(user=user, product=product)
    
    cart_item.quantity += 1
    cart_item.save()

    amount = Cart.objects.filter(user=user).annotate(
        total_value=F('quantity') * F('product__discounted_price')
    ).aggregate(total=Sum('total_value'))['total'] or 0

    shipping = 40.00
    totalamount = amount + shipping

    data = {
        'quantity': cart_item.quantity,
        'amount': amount,
        'totalamount': totalamount
    }

    return JsonResponse(data)


def minus_cart(request):
    if request.method == 'GET':
        prod_id = request.GET['prod_id']
        c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
        c.quantity -= 1
        c.save()
        user = request.user
        amount = 0.0
        cart = Cart.objects.filter(user=user)
        for p in cart:
            value = (p.quantity * p.product.discounted_price)
            amount = amount + value
        totalamount = amount + 40

        data = {
            'quantity': c.quantity,
            'amount': amount,
            'totalamount': totalamount
        }
        return JsonResponse(data)
    

def remove_cart(request):
    if request.method == 'GET':
        prod_id = request.GET['prod_id']
        c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
        c.delete()
        user = request.user
        amount = 0.0
        cart = Cart.objects.filter(user=user)
        for p in cart:
            value = (p.quantity * p.product.discounted_price)
            amount = amount + value
        totalamount = amount + 40

        data = {
            'amount': amount,
            'totalamount': totalamount
        }
        return JsonResponse(data)



