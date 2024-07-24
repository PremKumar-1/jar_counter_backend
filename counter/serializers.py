# serializers.py
"""from rest_framework import serializers
from .models import JarCount, Inventory

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = '__all__'

class JarCountSerializer(serializers.ModelSerializer):
    inventory_name = serializers.CharField(source='inventory.product_name', read_only=True)

    class Meta:
        model = JarCount
        fields = ['id', 'count', 'shift', 'timestamp', 'inventory', 'inventory_name']
"""

from rest_framework import serializers
from .models import JarCount, ShiftTiming, Inventory

class JarCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = JarCount
        fields = ['id', 'count', 'timestamp']

class ShiftTimingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftTiming
        fields = ['id', 'shift1_start', 'shift2_start']

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['id', 'product_name', 'quantity']
