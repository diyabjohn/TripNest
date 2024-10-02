# models.py
from django.db import models
from django.contrib.auth.models import User

class Hotel(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    amenities = models.TextField()
    rating = models.FloatField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    reviews = models.TextField()
    image = models.ImageField(upload_to='hotel_images/', blank=True, null=True)  # Add ImageField
    latitude = models.FloatField(null=True, blank=True)  # Add latitude field
    longitude = models.FloatField(null=True, blank=True)  # Add longitude field

    def __str__(self):
        return self.name

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} booked {self.hotel.name}'
    

