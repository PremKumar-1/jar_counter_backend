"""from django.db import models

class Inventory(models.Model):
    PRODUCT_CHOICES = [
        ('Jars', 'Jars'),
        ('Lids', 'Lids'),
        ('Labels', 'Labels'),
        ('Boxes', 'Boxes'),
        ('Sugar', 'Sugar'),
        ('Salt', 'Salt'),
        ('Soy', 'Soy'),
        ('Peanuts', 'Peanuts')
    ]

    product_name = models.CharField(max_length=100, choices=PRODUCT_CHOICES, unique=True)
    quantity = models.FloatField()  # Use FloatField to handle fractional quantities

    def __str__(self):
        return f"{self.product_name} - {self.quantity:.2f} items"

class JarCount(models.Model):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, null=True, blank=True)
    count = models.IntegerField()
    shift = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['shift']),
        ]

    def __str__(self):
        return f"{self.count} jars at {self.timestamp} during {self.shift} shift"
"""

from django.db import models

class Inventory(models.Model):
    PRODUCT_CHOICES = [
        ('Jars', 'Jars'),
        ('Lids', 'Lids'),
        ('Labels', 'Labels'),
        ('Boxes', 'Boxes'),
        ('Sugar', 'Sugar'),
        ('Salt', 'Salt'),
        ('Soy', 'Soy'),
        ('Peanuts', 'Peanuts')
    ]

    product_name = models.CharField(max_length=100, choices=PRODUCT_CHOICES, unique=True)
    quantity = models.FloatField()  # Use FloatField to handle fractional quantities

    def __str__(self):
        return f"{self.product_name} - {self.quantity:.2f} items"

class JarCount(models.Model):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, null=True, blank=True)
    count = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.count} jars at {self.timestamp}"

class ShiftTiming(models.Model):
    shift1_start = models.TimeField(default="08:00")
    shift2_start = models.TimeField(default="20:00")

    def __str__(self):
        return f"Shift 1 starts at {self.shift1_start}, Shift 2 starts at {self.shift2_start}"
