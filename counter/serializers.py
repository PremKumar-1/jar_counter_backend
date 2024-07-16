# serializers.py
from rest_framework import serializers
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
