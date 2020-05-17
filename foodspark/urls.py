from django.conf.urls import url
from django.urls import path
from .views import initiate_payment, callback
from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^login/?$', views.login, name='login'),
    url(r'^logout/?$', views.logout, name='logout'),
    url(r'^home/?$',views.home, name='home'),
    url(r'^dbhome/?$',views.home, name='home'),
    url(r'^signup/?$', views.signup, name='signup'),
    url(r'^search/?$',views.search,name='search'),
    url(r'^details/?$',views.details,name='details'),
    url(r'^dbdetails/?$',views.details,name='dbdetails'),
    url(r'^savedetails/?$',views.editDetails,name='editDetails'),
    url(r'^addtocart/cart/?$',views.cart,name='cart'),
    url(r'^cart/?$',views.cart,name='cart'),
    url(r'^history/?$',views.history,name='history'),
    url(r'^addrating/(?P<restname>[a-zA-Z0-9\s]+)/?$',views.restrating,name='restrating'),
    url(r'^dbhistory/?$',views.dbhistory,name='dbhistory'),
    url(r'^addtocart/?$',views.saveToCart,name='saveToCart'),
    url(r'^ratings/?$',views.ratings,name='ratings'),
    url(r'^restprofile/?$',views.restprofile,name='restprofile'),
    url(r'^resthistory/?$',views.restaurantOrderHistory,name='resthistory'),
    url(r'^delivered/?$',views.delivered,name='delivered'),
    url(r'^accepted/?$',views.accepted,name='accepted'),
    url(r'^declined/?$',views.declined,name='declined'),
    url(r'^decide/?$',views.decide,name='decide'),
    url(r'^onway/?$',views.onway,name='onway'),
    url(r'^addfooditem/?$',views.addfooditem,name='addfooditem'),
    url(r'^removefooditem/?$',views.removefooditem,name='removefooditem'),
    url(r'^callback/?$', views.callback, name='callback'),
    url(r'^addtocart/pay/?$', views.initiate_payment, name='pay'),
    # url(r'^makepaymenet/?$'.views.makepaymenet,name='makepaymenet'),
    url(r'^restaurant/(?P<restname>[a-zA-Z0-9\s]+)/?$',views.restview,name='restview'),
    url(r'^about/?$',views.about,name='about'),

    url(r'^deleteAccount/?$',views.deleteAccount,name='deleteAccount'),
    url(r'^forget_password/?$',views.otp_sent,name='forget_password'),
    url(r'^email/?$',views.email,name='email'),
]

