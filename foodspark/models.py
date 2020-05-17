from __future__ import unicode_literals

from django.db import models
from django.core.validators import RegexValidator
import hashlib
from django.contrib.auth import get_user_model
from django.core.validators import  *
from django.core.exceptions import ValidationError
import datetime

# default order time bug hai
User = get_user_model()

class Transaction(models.Model):
    #made_by = models.ForeignKey(Customer, related_name='transactions', on_delete=models.CASCADE)
    made_by = models.EmailField(max_length=100)
    made_on = models.DateTimeField(auto_now_add=True)
    amount = models.IntegerField()
    order_id = models.CharField(unique=True, max_length=100, null=True, blank=True)
    checksum = models.CharField(max_length=10000, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.order_id is None and self.made_on and self.id:
            self.order_id = self.made_on.strftime('PAY2ME%Y%m%dODR') + str(self.id)
        return super().save(*args, **kwargs)
        
class Restaurant(models.Model):
        email = models.EmailField(primary_key = True)
        password = models.CharField(max_length=100)
        name = models.CharField(max_length=200)
        address = models.TextField()
        RES_TYPE = (
                ('B','Bar'),
                ('R','Restaurant'),
                ('C','Cafe')
        )
        res_type = models.CharField(max_length=1,choices = RES_TYPE,default = 'R')
        cuisine = models.CharField(null = True, max_length=100)
        # RATING = (
        # 	('1','1'),
        # 	('2','2'),
        # 	('3','3'),
        # 	('4','4'),
        # 	('5','5')
        # )
        # rating = models.CharField(null = True,max_length=1,choices = RATING)
        # countrating = models.IntegerField(default = 0)
        city = models.CharField(max_length = 100,null = True)
        phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.") #############look into regex
        phone = models.CharField(validators=[phone_regex],max_length=15,blank = True)
        #image = models.ImageField(default = '/home/projjal/Projects/Foodspark/foodspark/static/img')
        imgurl = models.CharField(max_length=1000,null=True)
         ############################################################
        def make_password(self ,password):
                assert password
                password = password.encode('UTF-8')
                hashedpassword = hashlib.md5(password).hexdigest()
                return hashedpassword
        def check_password(self, password):
                assert password
                password = password.encode('UTF-8')
                hashed = hashlib.md5(password).hexdigest()
                return self.password == hashed
        def set_password(self, password):
                self.password = password

class Customer(models.Model):
        # userid = models.CharField(primary_key = True,max_length =50)
        password = models.CharField(max_length=100)
        name = models.CharField(max_length=200)
        address = models.TextField()
        city = models.CharField(max_length = 100)
        email = models.EmailField(primary_key = True)
        phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.") #############look into regex
        phone = models.CharField(validators=[phone_regex],max_length=15,blank = True)
        def make_password(self ,password):
                assert password
                password = password.encode('UTF-8')
                hashedpassword = hashlib.md5(password).hexdigest()
                return hashedpassword
        def check_password(self, password):
                assert password
                password = password.encode('UTF-8')
                hashed = hashlib.md5(password).hexdigest()
                return self.password == hashed
        def set_password(self, password):
                self.password = password

class DeliveryBoy(models.Model):
        # userid = models.CharField(primary_key = True,max_length =50)
        password = models.CharField(max_length=100)
        name = models.CharField(max_length=200)
        address = models.TextField()
        city = models.CharField(max_length = 100)
        email = models.EmailField(primary_key = True)
        phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.") #############look into regex
        phone = models.CharField(validators=[phone_regex],max_length=15,blank = True)
        def make_password(self ,password):
                assert password
                password = password.encode('UTF-8')
                hashedpassword = hashlib.md5(password).hexdigest()
                return hashedpassword
        def check_password(self, password):
                assert password
                password = password.encode('UTF-8')
                hashed = hashlib.md5(password).hexdigest()
                return self.password == hashed
        def set_password(self, password):
                self.password = password

class FoodItem(models.Model):
        resid = models.ForeignKey(Restaurant,on_delete=models.CASCADE)
        name = models.CharField(max_length=500)
        cuisine = models.CharField(max_length=100)
        COURSE = (
                ('s','Starter'),
                ('m','Main Course'),
                ('d','Desert')
        )
        course = models.CharField(max_length=1,choices=COURSE)
        price = models.IntegerField()
        availability_time = models.TimeField()
        ordercount = models.IntegerField(default = 0)
        # image = models.ImageField(null = True) ###########################################################
        # group = models.ForeignKey()

class Order(models.Model):
        customer = models.ForeignKey(Customer,on_delete=models.CASCADE)
        restaurant = models.ForeignKey(Restaurant,on_delete=models.CASCADE)
        foodlist = models.CharField(max_length = 500,validators=[validate_comma_separated_integer_list],null=True)
        foodqty = models.CharField(max_length = 500,validators=[validate_comma_separated_integer_list],null=True)
        amount = models.IntegerField(default = 0)
        ordertime = models.TimeField()
        orderdate = models.DateField(auto_now_add=True)	
        DSTATUS = (
                ('p','Pending'),
                ('d','Delivered')
        )
        deliverystatus = models.CharField(max_length=1,choices=DSTATUS,default = 'p')

        def calamount(self):
                self.amount = 0
                myl = self.foodlist.split(",")
                qty = self.foodqty.split(",")
                for x,y in zip(myl,qty):
                        fitem = FoodItem.objects.get(pk=int(x))
                        self.amount = self.amount + fitem.price*int(y)

        def getfooditems(self):
                myl = self.foodlist.split(",")
                items = []
                for x in myl:
                        items.append(FoodItem.objects.get(pk=int(x)))
                return items

        def getqty(self):
                myl = self.foodqty.split(",")
                return myl

class Cart(models.Model):
        customer = models.ForeignKey(Customer,on_delete=models.CASCADE)
        fooditem = models.ForeignKey(FoodItem,on_delete=models.CASCADE)
        foodqty = models.IntegerField()

class DeliveryItem(models.Model):
        deliveryboy_id = models.EmailField(null=True,default='')
        order_id = models.ForeignKey(Order,on_delete=models.CASCADE)
        DSTATUS = (
                ('p','Pending'),
                ('d','Delivered')
        )
        deliverystatus = models.CharField(max_length=1,choices=DSTATUS,default = 'p')
        #deliverystatus = models.ForeignKey(Order,on_delete=models.CASCADE)

class Ratings(models.Model):
        restid = models.ForeignKey(Restaurant,on_delete=models.CASCADE)
        custid = models.ForeignKey(Customer,on_delete=models.CASCADE)
        rating = models.IntegerField(null=True)
        review = models.CharField(max_length=1000,null=True)
        #deliverystatus = models.ForeignKey(Order,on_delete=models.CASCADE)

class Temp(models.Model):
        custid=models.ForeignKey(Customer,on_delete=models.CASCADE)
        amount=models.IntegerField(null=True)

class Locuser(models.Model):
        #custid=models.ForeignKey(Customer,on_delete=models.CASCADE)
        custid=models.EmailField()
        address_user=models.CharField(max_length=1000,null=True)

class Locrest(models.Model):
        restid=models.EmailField()
        address_rest=models.CharField(max_length=1000,null=True)