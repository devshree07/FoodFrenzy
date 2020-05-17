from django.shortcuts import get_object_or_404,render, redirect
from django.http import HttpResponse
from .models import *
import json
from django.views.decorators import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from django.core.exceptions import *
import datetime
from django.shortcuts import render
from django.contrib.auth import authenticate, login as auth_login
from django.conf import settings
from .models import Transaction
from .paytm import generate_checksum, verify_checksum
from django.views.decorators.csrf import csrf_exempt
from django.utils.datastructures import MultiValueDictKeyError

from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import numpy as np
import math, random
import smtplib 
import statistics
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders

def initiate_payment(request):
	if request.method == "GET":
		user1=Customer.objects.get(email=request.session['id'])
		t = Temp.objects.get(custid_id=user1.email)
		amount=t.amount
		return render(request,'foodspark/pay.html',{'amount':amount})
	try:
		if 'id' in request.session.keys():
			if request.session['type'] == 'customer':
				email = request.POST['username']
				password = request.POST['password']
				'''
				print('hi')
				print(amount)
				print("hi")'''
				
				try:
					customer = Customer.objects.get(email=email)
					if customer.check_password(password):
						request.session['id'] = email
						request.session['type'] = 'customer'
						#return redirect('/')
					else:
						messages.error(request,'Password Incorrect')
						return render(request, 'foodspark/pay.html', context={'error': 'Wrong Account Details or amount'})
				except:
					return redirect('/')
		
				'''
				user = authenticate(request, username=email, password=password)
				if user is None:
					raise ValueError
				auth_login(request=request, user=user)'''
	except:
		return render(request, 'foodspark/pay.html', context={'error': 'Wrong Account Details or amount'})
	user1=Customer.objects.get(email=request.session['id'])
	t = Temp.objects.get(custid_id=user1.email)
	amount=t.amount
	transaction = Transaction.objects.create(made_by=email, amount=amount)
	transaction.save()
	merchant_key = settings.PAYTM_SECRET_KEY

	params = (
		('MID', settings.PAYTM_MERCHANT_ID),
		('ORDER_ID', str(transaction.order_id)),
		('CUST_ID', str(transaction.made_by)),
		('TXN_AMOUNT', str(transaction.amount)),
		('CHANNEL_ID', settings.PAYTM_CHANNEL_ID),
		('WEBSITE', settings.PAYTM_WEBSITE),
	# ('EMAIL', request.user.email),
	# ('MOBILE_N0', '9911223388'),
		('INDUSTRY_TYPE_ID', settings.PAYTM_INDUSTRY_TYPE_ID),
		('CALLBACK_URL', 'http://127.0.0.1:8000/callback/'),
	# ('PAYMENT_MODE_ONLY', 'NO'),
	)
	
	paytm_params = dict(params)
	checksum = generate_checksum(paytm_params, merchant_key)

	transaction.checksum = checksum
	transaction.save()

	paytm_params['CHECKSUMHASH'] = checksum
	print('SENT: ', checksum)
	return render(request, 'foodspark/redirect.html', context=paytm_params)


@csrf_exempt
def callback(request):
	if request.method == 'POST':
		form = request.POST
		response_dict = {}
		for i in form.keys():
			response_dict[i] = form[i]
			if i == 'CHECKSUMHASH':
				checksum = form[i]
		merchant_key = settings.PAYTM_SECRET_KEY
		verify = verify_checksum(response_dict, merchant_key, checksum)
		if verify:
			if response_dict['RESPCODE'] == '01':
				print('order successful')
			else:
				print('order was not successful because' + response_dict['RESPMSG'])
		return render(request, 'foodspark/callback.html', {'response': response_dict})


def home(request):
	if 'id' in request.session.keys():
		if request.session['type'] == 'customer':
			foodlist = FoodItem.objects.all().order_by('-ordercount')[:5]
			restaurants = Restaurant.objects.order_by('name')
			context = {
				'customer':Customer.objects.get(email=request.session['id']),
				'restaurants' : restaurants,
				'foodlist' : foodlist,
				'count' : 1
			}
			return render(request,'foodspark/userhome.html',context)
		elif request.session['type'] == 'deliveryboy':
			query = Order.objects.order_by('-pk').all()
			dic = {}
			customer = {}
			for x in query:
				dic2 = {}
				if(x.deliverystatus == 'd'):
					continue
				x.calamount()
				for i,j in zip(x.getfooditems(),x.getqty()):
					dic2[i] = j
				dic[x] = dic2
				customer[x] = x.customer
			print("Orders")
			print(dic)
			context = {
				'foods' : dic,
				'deliveryboy' : DeliveryBoy.objects.get(email=request.session['id']),
				'customer': customer
			}
			return render(request,'foodspark/dbhome.html',context)

		elif request.session['type'] == 'restaurant':
			restaurant = Restaurant.objects.get(email=request.session['id'])
			query = Order.objects.order_by('-pk').all()
			dic = {}
			customer = {}
			for x in query:
				if x.restaurant_id == restaurant.email:
					dic2 = {}
					if(x.deliverystatus == 'd'):
						continue
					x.calamount()
					for i,j in zip(x.getfooditems(),x.getqty()):
						dic2[i] = j
					dic[x] = dic2
					customer[x] = x.customer

			context = {
				'foods' : dic,
				'customer' : customer,
				'restaurant' : restaurant,
			}

			return render(request,'foodspark/resthome.html',context)
	else:
		return render(request,"foodspark/login.html")

@ensure_csrf_cookie
def login(request):
	print("hello")
	if request.method == 'POST':
		email = request.POST.get('email')
		password = request.POST.get('password')
		try:
			customer = Customer.objects.get(email=email)
			if customer.check_password(password):
				request.session['id'] = email
				request.session['type'] = 'customer'
				return redirect('/')
			else:
				messages.error(request,'Password Incorrect')
				return redirect('/')
		except:
			try:
				restaurant = get_object_or_404(Restaurant, email=email)
				if restaurant.check_password(password):
					request.session['id'] = email
					request.session['type'] = 'restaurant'
					return redirect('/')
				else:
					messages.error(request,'Password Incorrect')
					return redirect('/')
			except:
                                try:
                                        deliveryboy = DeliveryBoy.objects.get(email=email)
                                        if deliveryboy.check_password(password):
                                                request.session['id'] = email
                                                request.session['type'] = 'deliveryboy'
                                                return redirect('/')
                                        else:
                                                messages.error(request,'Password Incorrect')
                                                return redirect('/')
                                except:
                                        return redirect('/')

	elif request.method == 'GET':
		return render(request,'foodspark/login.html')

def signup(request):
	if request.method == 'POST':
		email = request.POST.get('email')
		name = request.POST.get('name')
		phone = request.POST.get('phone')
		password = request.POST.get('password')
		address = request.POST.get('address')
		usertype = request.POST.get('usertype')

		geolocator = Nominatim()
		loca = geolocator.geocode(address)
		print(loca.address)
		
		if usertype == 'Customer':
			user = Customer(name = name, email = email, phone = phone, address = address)
			user.set_password(user.make_password(password))
			user.save()
			request.session['id'] = email
			request.session['type'] = 'customer'

			#customer = Customer.objects.get(email=request.session['id'])
			l1=(loca.latitude,loca.longitude)
			t=Locuser()
			t.custid = email
			t.address_user = l1
			t.save()

		elif usertype == 'Restaurant':
			rest = Restaurant.objects.all()
			test=0
			for x in rest:
				if(x.name == name):
					messages.error(request,"Restaurant with this name already exists")
					test=1
					return render(request,'foodspark/login.html')
			if(test==0):
				user = Restaurant(name= name, email = email, phone = phone, address = address)
				user.set_password(user.make_password(password))
				user.save()
				request.session['id'] = email
				request.session['type'] = 'restaurant'

				l2=(loca.latitude,loca.longitude)
				t=Locrest()
				t.restid=email
				t.address_rest=l2
				t.save()

		elif usertype == 'DeliveryBoy':
			user = DeliveryBoy(name= name, email = email, phone = phone, address = address)
			user.set_password(user.make_password(password))
			user.save()
			request.session['id'] = email
			request.session['type'] = 'deliveryboy'
		return redirect('/')

	if request.method == 'GET':
		return render(request,'foodspark/login.html')

def logout(request):
	try:
		del request.session['id']
		del request.session['type']
		request.session.modified = True
	except KeyError:
		pass
	return render(request, 'foodspark/login.html')

def editDetails(request):
	if request.method == 'POST':
		if request.session['type'] == 'customer':
			customer = Customer.objects.get(email=request.session['id'])
			context = {
				'customer':customer,
				}
			name = request.POST.get('name')
			phone = request.POST.get('phone')
			address = request.POST.get('address')
			city = request.POST.get('city')
			password = request.POST.get('password')
			print("ADDRESS")
			print(address)
			if name!="":
				customer.name = name
			if address!="":
				customer.address = address
				geolocator = Nominatim()
				loca = geolocator.geocode(address)
				print(loca.address)
				l1=(loca.latitude,loca.longitude)
				t=Locuser.objects.get(custid=request.session['id'])
				t.address_user = l1
				t.save()
			if city!="":
				customer.city	= city
			if phone!="":
				customer.phone = phone
			if password!="":
				customer.set_password(customer.make_password(password))
			customer.save()

			

			messages.success(request,'Successfully saved :)')
			return render(request,'foodspark/userdetails.html',context)
		elif request.session['type'] == 'deliveryboy':
			deliveryboy = DeliveryBoy.objects.get(email=request.session['id'])
			context = {
                    'deliveryboy':deliveryboy,
                    }
			name = request.POST.get('name')
			phone = request.POST.get('phone')
			address = request.POST.get('address')
			city = request.POST.get('city')
			if name!="":
				deliveryboy.name = name
			if address!="":
				deliveryboy.address = address
			if city!="":
				deliveryboy.city = city
			if phone!="":
				deliveryboy.phone = phone
			deliveryboy.save()
			messages.success(request,'Successfully saved :)')
			return render(request,'foodspark/dbdetails.html',context)
		elif request.session['type'] == 'restaurant':
			restaurant = Restaurant.objects.get(email=request.session['id'])
			context = {
				'restaurant' : restaurant,
			}
			name = request.POST.get('name')
			phone = request.POST.get('phone')
			address = request.POST.get('address')
			res_type = request.POST.get('res_type')
			cuisine = request.POST.get('cuisine')
			city = request.POST.get('city')

			if phone!="":
				restaurant.phone = phone
			if address!="":
				restaurant.address = address
			if name!="":
				restaurant.name = name
			# restaurant.res_type = res_type
			if cuisine!="":
				restaurant.cuisine =cuisine
			if city!="":
				restaurant.city = city
			restaurant.save()
			messages.success(request,'Successfully saved :)')
			return render(request,'foodspark/restdetails.html',context)

	elif request.method == 'GET':
		return render(request,'foodspark/details.html')

def changePassword(request):
	if request.method == "POST":
		if request.session['type'] == 'customer':
			customer = Customer.objects.get(email=request.session['id'])
			oldPassword = request.POST.get('oldPassword')
			newPassword = request.POST.get('newPassword')
			if customer.check_password(oldPassword):
				customer.set_password(customer.make_password(newPassword))
				messages.success(request,"Password Successfully Changed")
				customer.save()
			else:
				messages.error(request,"Old password is incorrect")
			return render(request,'foodspark/changePassword.html')
		elif request.session['type'] == 'deliveryboy':
			deliveryboy = DeliveryBoy.objects.get(email=request.session['id'])
			oldPassword = request.POST.get('oldPassword')
			newPassword = request.POST.get('newPassword')
			if deliveryboy.check_password(oldPassword):
				deliveryboy.set_password(deliveryboy.make_password(newPassword))
				messages.success(request,"Password Successfully Changed")
				deliveryboy.save()
			else:
				messages.error(request,"Old password is incorrect")
			return render(request,'foodspark/changePassword.html')
		elif request.session['type'] == 'restaurant':
			restaurant = Restaurant.objects.get(email=request.session['id'])
			oldPassword = request.POST.get('oldPassword')
			newPassword = request.POST.get('newPassword')
			if restaurant.check_password(oldPassword):
				restaurant.set_password(restaurant.make_password(newPassword))
				messages.success(request,"Password Successfully Changed")
				restaurant.save()
			else:
				messages.error(request,"Old password is incorrect")
			return render(request,'foodspark/changePassword.html')

	elif request.method == 'GET':
		return render(request,'foodspark/changePassword.html')


def search(request):
	searchkey = request.POST.get('search')
	searchtype = request.POST.get('search_param')
	print("SEARCH")
	print(searchkey)
	print(searchtype)
	if searchtype == 'Restaurant':
		restaurants = Restaurant.objects.filter(name__contains=searchkey)
	elif searchtype == 'Cuisine':
		foods = FoodItem.objects.filter(cuisine__contains=searchkey)
		restaurants = []
		for x in foods:
			if x.resid not in restaurants:
				restaurants.append(x.resid)
	elif searchtype == 'Food':
		foods = FoodItem.objects.filter(name__contains=searchkey)
		restaurants = []
		for x in foods:
			if x.resid not in restaurants:
				restaurants.append(x.resid)
	elif searchtype == 'City':
		print(searchkey)
		restaurants = Restaurant.objects.filter(city__contains=searchkey)
	elif searchtype == 'All':
		restaurants = Restaurant.objects.filter(name__contains=searchkey)
		restaurants = list(restaurants)
		
		foods_cuisine = FoodItem.objects.filter(cuisine__contains=searchkey)
		print(foods_cuisine)
		foods = FoodItem.objects.filter(name__contains=searchkey)
		for x in foods:
			if x.resid not in restaurants:
				restaurants.append(x.resid)
		for x in foods_cuisine:
			if x.resid not in restaurants:
				restaurants.append(x.resid)
		rescity = Restaurant.objects.filter(city__contains=searchkey)
		rescity = list(rescity)
		for i in rescity:
			if i not in restaurants:
				restaurants.append(i)
		print(restaurants)
	count=0
	context = {
		'customer':Customer.objects.get(email=request.session['id']),
		'rest' : restaurants,
		'searchkey' : searchkey,
		'count' : count
	}
	return render(request,'foodspark/userhome.html',context)

def restaurantOrderHistory(request):
	restaurant = Restaurant.objects.get(email=request.session['id'])
	query = Order.objects.order_by('-pk').all()
	dic = {}
	customer = {}
	for x in query:
		if x.restaurant_id == restaurant.email:
			dic2 = {}
			if(x.deliverystatus == 'p'):
				continue
			x.calamount()
			for i,j in zip(x.getfooditems(),x.getqty()):
				dic2[i] = j
			dic[x] = dic2
			customer[x] = x.customer

	context = {
		'foods' : dic,
		'customer' : customer,
		'restaurant' : restaurant,
	}

	return render(request,'foodspark/resthistory.html',context)

def amt(request,amount):
	customer=Customer.objects.get(email=request.session['id'])
	Temp.objects.filter(custid_id=customer.email).delete()
	#customer=Customer.objects.get(email=request.session['id'])
	t=Temp(custid_id=customer.email,amount=amount)
	t.save()

def ratings(request):
	restaurant = Restaurant.objects.get(email=request.session['id'])
	ratings=Ratings.objects.filter(restid=restaurant.email)
	dic1={}
	dic2={}
	dic3={}
	customer = {}
	list1={}
	i=0
	for x in ratings:
		c1=Customer.objects.get(email=x.custid_id)
		temp1=('Name:  '+c1.name)
		temp2=('Rating:  '+str(x.rating))
		temp3=('Review:  '+str(x.review))
		customer.setdefault(i,[]).append(temp1)
		customer.setdefault(i,[]).append(temp2)
		customer.setdefault(i,[]).append(temp3)
		'''dic1[x]=x.rating
		dic2[x]=x.review
		dic3[x]=c1.name'''
		i=i+1
	#list=[dic1,dic2,dic3]
	context = {
		'customer' : customer,
		'restaurant' : restaurant
	}
	print(context)
	return render(request,'foodspark/ratings.html',context)

def restprofile(request):
	restaurant = Restaurant.objects.get(email=request.session['id'])
	fooditems = FoodItem.objects.all()
	menu = {}
	for fi in fooditems:
		if fi.resid == restaurant:
			try:
				menu[fi.cuisine].append(fi)
			except KeyError:
				menu[fi.cuisine] = [fi]
	context = {
		'restaurant' : restaurant,
		'menu' : menu
	}
	return render(request,'foodspark/restprofile.html',context)

def restview(request,restname):
	if 'id' in request.session.keys():
		try:
			customer = Customer.objects.get(email=request.session['id'])
			print(customer.email)
			restaurant =Restaurant.objects.get(name=restname)
			print(restaurant.name)
			foodall = FoodItem.objects.all()

			recall = FoodItem.objects.all().order_by('-ordercount')[:5]

			add1=Locuser.objects.get(custid=request.session['id'])
			add_user=eval(add1.address_user)
			add2=Locrest.objects.get(restid=restaurant.email)
			add_rest=eval(add2.address_rest)
			distance=geodesic(add_user,add_rest).kilometers
			print(distance)
			speed=30
			eta=str(float(distance/speed))
			
			ratings=Ratings.objects.filter(restid_id=restaurant.email)
			count=0
			sum1=0
			for x in ratings:
				sum1=sum1+x.rating
				count=count+1
			if count==0:
				mean_ratings='NA'
			else:
				mean_ratings=str(float(sum1/count))
			fooditems = {}
			for x in foodall:
				if x.resid.email == restaurant.email:
					try:
						fooditems[x.cuisine].append(x)
					except KeyError:
						fooditems[x.cuisine] = [x]
			
			recitems = []
			for x in recall:
				if x.resid.email == restaurant.email:
					try:
						recitems.append(x.name)
					except KeyError:
						recitems = [x.name]
			print(recitems)
			context = {
				'customer' : customer,
				'restaurant': restaurant,
				'fooditems' : fooditems,
				'recitems' : recitems,
				'distance' : round(distance,2),
				'mean_ratings' : mean_ratings
			}
			return render(request,'foodspark/restview.html',context)
		except ObjectDoesNotExist:
			return HttpResponse("Sorry no restaurant with this name")
	else:
		return redirect('/')

def cart(request):
	if 'id' in request.session.keys():
		print(request.method)
		if request.method == 'GET':
			print('hello1')
			customer = Customer.objects.get(email=request.session['id'])
			query = Cart.objects.all()
			cart = {}
			amount = 0
			for x in query:
				if x.customer.email == customer.email:
					amount = amount + x.fooditem.price * x.foodqty
					try:
						cart[x.fooditem.resid].append(x)
					except KeyError:
						cart[x.fooditem.resid] = [x]

			if not cart:
				messages.info(request,"Your cart is currently empty")
			context = {
					'customer': customer,
					'cart' : cart,
					'amount' : amount
			}
			return render(request,"foodspark/ordercart.html",context)
		elif request.method == 'POST':
			########delete cart update order
			print('hello2')
			customer = Customer.objects.get(email=request.session['id'])
			orders = {}
			ordersqty = {}
			for q in Cart.objects.all():
				if q.customer == Customer.objects.get(email=request.session['id']):
					try:
						orders[q.fooditem.resid] = orders[q.fooditem.resid] + ',' + str(q.fooditem.pk)
					except KeyError:
						orders[q.fooditem.resid] = str(q.fooditem.pk)
					try:
						ordersqty[q.fooditem.resid] = ordersqty[q.fooditem.resid] + ',' + str(q.foodqty)
					except KeyError:
						ordersqty[q.fooditem.resid] = str(q.foodqty)
					q.delete()
			for x,y in zip(orders,ordersqty):
				o = Order(customer=customer,restaurant=x,foodlist=orders[x],foodqty=ordersqty[y],ordertime=datetime.datetime.now(),deliverystatus='p') 
				o.calamount()
				o.save()
				print("INN")
				print(o.pk)
				deli = DeliveryItem(deliverystatus='p', deliveryboy_id="", order_id_id=o.pk)
				deli.save()
			messages.success(request,"Payment Successfull :)")
			context = {
					'customer': customer
			}
			return render(request,"foodspark/ordercart.html")
		else:
			print('hello')
	else:
		return render(request,"foodspark/login.html")

def details(request):
	if 'id' in request.session.keys():
		if request.session['type'] == 'customer':
			context = {
				'customer':Customer.objects.get(email=request.session['id']),
			}
			return render(request,'foodspark/userdetails.html',context)
		elif request.session['type'] == 'restaurant':
			context = {
				'restaurant':Restaurant.objects.get(email=request.session['id'])
			}
			return render(request,'foodspark/restdetails.html',context)
		elif request.session['type'] == 'deliveryboy':
			context = {
				'deliveryboy':DeliveryBoy.objects.get(email=request.session['id'])
			}
			return render(request,'foodspark/dbdetails.html', context)
	else:
		return render(request,"foodspark/login.html")

def history(request):
	if 'id' in request.session.keys():
		customer = Customer.objects.get(email=request.session['id'])
		query = Order.objects.order_by('-pk').all()
		pending_rest = {}
		pending_items = {}
		reject_rest = {}
		reject_items = {}
		history_rest = {}
		history_items = {}
		eta={}
		
		#print(distance)
		
		for x in query:
			if x.customer == customer:
				if(x.deliverystatus == 'p' or x.deliverystatus == 'a' or x.deliverystatus == 'o'):
					print("1")
					dic2 = {}
					x.calamount()
					for i,j in zip(x.getfooditems(),x.getqty()):
						dic2[i] = j
					pending_items[x] = dic2
					pending_rest[x] = x.restaurant
					add1=Locuser.objects.get(custid=request.session['id'])
					add_user=eval(add1.address_user)
					add2=Locrest.objects.get(restid=x.restaurant_id)
					add_rest=eval(add2.address_rest)
					distance=geodesic(add_user,add_rest).kilometers
					speed=30
					eta[x]=str(round(float(distance/speed)*60,2))
					print(eta)
				if(x.deliverystatus == 'd'):
					dic2 = {}
					x.calamount()
					for i,j in zip(x.getfooditems(),x.getqty()):
						dic2[i] = j
					history_items[x] = dic2
					history_rest[x] = x.restaurant
				if(x.deliverystatus == 'r'):
					dic3 = {}
					x.calamount()
					for i,j in zip(x.getfooditems(),x.getqty()):
						dic3[i] = j
					reject_items[x] = dic3
					reject_rest[x] = x.restaurant


		context = {
			'customer' : customer,
			'pending_items' : pending_items,
			'pending_rest' : pending_rest,
			'history_items' : history_items,
			'history_rest' : history_rest,
			'reject_items' : reject_items,
			'reject_rest' : reject_rest,
			'eta' : eta
		}
		return render(request,"foodspark/userhistory.html",context)
	else:
		return render(request,"foodspark/login.html")

def dbhistory(request):
	
	boy = DeliveryBoy.objects.get(email=request.session['id'])
	delivery=DeliveryItem.objects.filter(deliveryboy_id=boy.email)
	#query = Order.objects.order_by('-pk').all()
	print("DELIVERY")
	print(delivery)
	dic = {}
	customer = {}
	for deliveryboy in  delivery:
		print(deliveryboy.order_id_id)
		query1 = Order.objects.filter(id=deliveryboy.order_id_id)
		dic2 = {}
		for x in query1:
			dic2={}
			if(x.deliverystatus == 'p' or x.deliverystatus == 'a'):
				continue
			x.calamount()
			for i,j in zip(x.getfooditems(),x.getqty()):
				dic2[i] = j
			dic[x] = dic2
			customer[x] = x.customer
	context = {
		'foods' : dic,
		'customer' : customer,
		'deliveryboy' : boy,
	}
	return render(request,"foodspark/dbhistory.html",context)

def recommendedRests():
	pass

def saveToCart(request):
	if 'id' in request.session.keys():
		Cart.objects.all().delete()
		foodall = FoodItem.objects.all()
		for x in foodall:
			if 'food' + str(x.pk) in request.POST.keys():
				if int(request.POST['food' + str(x.pk)]) > 0:
					cartitem = Cart(customer = Customer.objects.get(email=request.session['id']), fooditem = FoodItem.objects.get(pk=x.pk), foodqty= request.POST['food' + str(x.pk)])
					cartitem.save()
		customer = Customer.objects.get(email=request.session['id'])
		query = Cart.objects.all()
		cart = {}
		amount = 0
		for x in query:
			if x.customer.email == customer.email:
				amount = amount + x.fooditem.price * x.foodqty
				try:
					cart[x.fooditem.resid].append(x)
				except KeyError:
					cart[x.fooditem.resid] = [x]
		if not cart:
			messages.info(request,"Your cart is currently empty")
		amt(request,amount)
		context = {
				'customer': customer,
				'cart' : cart,
				'amount' : amount
		}
		for x,y in cart.items():
			for z in y:
				z.fooditem.ordercount = z.fooditem.ordercount + z.foodqty
				z.fooditem.save()
		return render(request,"foodspark/ordercart.html",context)
	else:
		return render(request,"foodspark/login.html")

def delivered(request):
	print("ORDER ID")
	if 'id' in request.session.keys() and request.session['type'] == 'deliveryboy':
		#try:
		order = Order.objects.get(pk=request.POST['orderid1'])
		print("ORDER ID")
		print(order.id)
		#except:
		#	order = Order.objects.get(pk)
		order.deliverystatus = 'd'
		order.save()
		di = DeliveryItem.objects.get(order_id_id = order.pk)
		di.deliverystatus = 'd'
		di.save()
		return redirect('/')

	else:
		return render(request,"foodspark/login.html")

def accepted(request):
	if 'id' in request.session.keys() and request.session['type'] == 'restaurant':
		order = Order.objects.get(pk = request.POST['orderid'])
		print(order.pk)

		order.deliverystatus = 'a'
		order.save()
		di = DeliveryItem.objects.get(order_id_id = order.pk)
		di.deliverystatus = 'a'
		di.save()
		return redirect('/')

	else:
		return render(request,"foodspark/login.html")

def declined(request):
	if 'id' in request.session.keys() and request.session['type'] == 'restaurant':
		order = Order.objects.get(pk = request.POST['orderid'])
		print(order.pk)

		order.deliverystatus = 'r'
		order.save()
		'''di = DeliveryItem.objects.get(order_id_id = order.pk)
		di.deliverystatus = 'r'
		di.save()'''
		return redirect('/')

	else:
		return render(request,"foodspark/login.html")

def decide(request):
	if request.POST:
		if '_accept' in request.POST:
			accepted(request)
		elif '_decline' in request.POST:
			declined(request)
		return redirect('/')
	else:
		return render(request,"foodspark/userhome.html")

def onway(request):
	if 'id' in request.session.keys() and request.session['type'] == 'deliveryboy':
		order = Order.objects.get(pk = request.POST.get('orderid',False))
		if order.deliverystatus == 'a':
			order.deliverystatus = 'o'
		else:
			order.deliverystatus = 'd'
		order.save()

		deliveryboy = DeliveryBoy.objects.get(email=request.session['id'])
		#order_id = Order.objects.get(pk = request.POST['id'])
		di = DeliveryItem.objects.get(order_id_id = order.pk)
		if di.deliverystatus == 'a':
			di.deliverystatus = 'o'
		else:
			di.deliverystatus = 'd'
		
		di.deliveryboy_id = deliveryboy.email
		di.save()
		#DeliveryItem.order_id = order.id
		di.save()
		
		return redirect('/')

	else:
		return render(request,"foodspark/login.html")

def addfooditem(request):
	if 'id' in request.session.keys() and request.session['type'] == 'restaurant':
		restaurant = Restaurant.objects.get(email=request.session['id'])
		name = request.POST['name']
		cuisine = request.POST['cuisine']
		price = request.POST['price']
		food = FoodItem(resid=restaurant,name=name,cuisine=cuisine,price=price,course='s',availability_time=datetime.datetime.now())
		food.save()
		return redirect('/restprofile/')
	else:
		return render(request,"foodspark/login.html")

def removefooditem(request):
	if 'id' in request.session.keys() and request.session['type'] == 'restaurant':
		restaurant = Restaurant.objects.get(email=request.session['id'])
		food = FoodItem.objects.get(pk=request.POST['foodid'])
		food.delete()
		return redirect('/restprofile/')
	else:
		return render(request,"foodspark/login.html")

def about(request):
	if 'id' in request.session.keys():
		if request.session['type'] == 'restaurant':
			user = Restaurant.objects.get(email=request.session['id'])
		elif request.session['type'] == 'customer':
			user = Customer.objects.get(email=request.session['id'])
		else:
			user = DeliveryBoy.objects.get(email=request.session['id'])
		context = {
			'user': user,
		}
		return render(request,"foodspark/about.html",context)
	else:
		return render(request,"foodspark/about.html")

def acceptDelivery(request):
	if 'id' in request.session.keys() and request.session['type'] == 'deliveryboy':
		deliveryboy = DeliveryBoy.objects.get(email=request.session['id'])
		order_id = Order.objects.get(pk = request.POST['orderid'])
		DeliveryItem.deliveryboy = deliveryboy
		DeliveryItem.order_id = order_id
		DeliveryItem.save()
		context = {
				'deliveryboy': deliveryboy,
				'order_id' : order_id,
		}
		return render(request,"foodspark/dbdetails.html",context)
	else:
		return render(request,"foodspark/login.html")

def restrating(request,restname):
	if 'id' in request.session.keys() and request.session['type'] == 'customer':
		custid = Customer.objects.get(email=request.session['id'])
		restaurant =Restaurant.objects.get(name=restname)
		rating1 = Ratings.objects.filter(restid_id=restaurant.email ,custid_id=custid.email)
		print("LEN RATING")
		print(len(rating1))
		print(rating1)
		if(len(rating1)==0):
			food = Ratings(restid_id=restaurant.email ,custid_id=custid.email,rating=request.POST.get('rating'),review=request.POST.get('review'))
			food.save()
		else:
			food = Ratings.objects.get(restid_id=restaurant.email ,custid_id=request.session['id'])
			food.rating=request.POST.get('rating')
			food.review=request.POST.get('review')
			print(food.rating)
			print(food.review)
			food.save()
		return redirect('/')
	else:
		return render(request,"foodspark/login.html")

def deleteAccount(request):
	if 'id' in request.session.keys() and request.session['type'] == 'customer':
		Customer.objects.get(email=request.session['id']).delete()
	if 'id' in request.session.keys() and request.session['type'] == 'restaurant':
		Restaurant.objects.get(email=request.session['id']).delete()
	if 'id' in request.session.keys() and request.session['type'] == 'deliveryboy':
		DeliveryBoy.objects.get(email=request.session['id']).delete()
		return redirect(request,"foodspark/login.html")
	else:
		return render(request,"foodspark/login.html")

def email(request):
	return render(request,"foodspark/email.html")

def otp_sent(request):
	if request.method == 'POST':
		email = request.POST.get('email')
		try:	
			customer = Customer.objects.get(email=email)
			digits = "0123456789"
			OTP = ""
			for i in range(4) :
				OTP += digits[math.floor(random.random() * 10)]
			customer.set_password(customer.make_password(OTP))
			customer.save()
			msg = MIMEMultipart() 
			msg['Subject'] = "This is your new password"
			body = OTP
			msg.attach(MIMEText(str(body), 'plain'))
			s = smtplib.SMTP('smtp.gmail.com', 587)
			# start TLS for security
			s.starttls()
			print("HELLOOOO")
			# Authentication
			s.login("foodfrenzy18@gmail.com", "cjqzmzhdiuhiescg")
			# message to be sent
			#message = "This is your new password: " + str(OTP)
			# sending the mail
			print("HELLO3")
			s.sendmail("foodfrenzy18@gmail.com", email, str(msg))
			# terminating the session
			s.quit()
			return render(request,"foodspark/login.html")
		except:
			return HttpResponse("Sorry no user with this email")
			