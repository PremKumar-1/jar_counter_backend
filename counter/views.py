"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.dateparse import parse_date
import json
from datetime import datetime
from .models import JarCount, Inventory
from .serializers import JarCountSerializer, InventorySerializer

class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer

    def create(self, request, *args, **kwargs):
        # Custom create method to handle updates for existing inventory items
        inventory_data = request.data if isinstance(request.data, list) else [request.data]
        response_data = []
        for item in inventory_data:
            product_name = item.get('product_name')
            quantity = item.get('quantity')
            try:
                inventory_item, created = Inventory.objects.update_or_create(
                    product_name=product_name,
                    defaults={'quantity': quantity}
                )
                response_data.append({
                    'product_name': inventory_item.product_name,
                    'quantity': inventory_item.quantity,
                    'status': 'created' if created else 'updated'
                })
            except Exception as e:
                return Response({'status': 'error', 'message': str(e)}, status=400)
        return Response(response_data, status=201)

class JarCountViewSet(viewsets.ModelViewSet):
    queryset = JarCount.objects.all()
    serializer_class = JarCountSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        date = self.request.query_params.get('date')
        if date:
            date = parse_date(date)
            if date:
                queryset = queryset.filter(timestamp__date=date)
        return queryset

    @action(detail=False, methods=['post'])
    def update_inventory(self, request):
        try:
            count = int(request.data.get('count'))
            shift = request.data.get('shift')
            inventory_id = request.data.get('inventory_id')

            inventory = Inventory.objects.get(id=inventory_id)

            depletion_rates = {
                'Jars': 1,
                'Lids': 1,
                'Labels': 1,
                'Sugar': 0.077,
                'Salt': 0.011,
                'Soy': 0.031,
                'Peanuts': 1.173,
                'Boxes': 1/12
            }

            required_quantity = count * depletion_rates[inventory.product_name]
            if inventory.quantity < required_quantity:
                return Response({'status': 'error', 'message': f'Insufficient {inventory.product_name}'})

            inventory.quantity -= required_quantity
            inventory.save()

            JarCount.objects.create(inventory=inventory, count=count, shift=shift)
            return Response({'status': 'success', 'message': 'Inventory updated and jars counted'})
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def update_jar_count(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            jar_count = data.get('jar_count')
            shift = data.get('shift')
            timestamp = data.get('timestamp')

            depletion_rates = {
                'Jars': 1,
                'Lids': 1,
                'Labels': 1,
                'Sugar': 0.077,
                'Salt': 0.011,
                'Soy': 0.031,
                'Peanuts': 1.173,
                'Boxes': 1/12
            }

            if jar_count is not None and shift:
                for item, rate in depletion_rates.items():
                    inventory_item, created = Inventory.objects.get_or_create(product_name=item)
                    inventory_item.quantity -= jar_count * rate
                    inventory_item.save()

                JarCount.objects.create(
                    count=jar_count,
                    shift=shift,
                    timestamp=timezone.now()
                )

                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'fail', 'reason': 'Invalid data'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'fail', 'reason': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'fail', 'reason': str(e)}, status=400)
    elif request.method == 'GET':
        return JsonResponse({'status': 'info', 'message': 'Use POST to update jar count'}, status=200)
    else:
        return JsonResponse({'status': 'fail', 'reason': 'Invalid request method'}, status=405)
"""
from rest_framework import viewsets, pagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Sum
import json
from datetime import datetime
from .models import JarCount, Inventory
from .serializers import JarCountSerializer, InventorySerializer
from django.utils.timezone import make_aware
import pytz

class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer

    def create(self, request, *args, **kwargs):
        inventory_data = request.data if isinstance(request.data, list) else [request.data]
        response_data = []
        for item in inventory_data:
            product_name = item.get('product_name')
            quantity = item.get('quantity')
            try:
                inventory_item, created = Inventory.objects.update_or_create(
                    product_name=product_name,
                    defaults={'quantity': quantity}
                )
                response_data.append({
                    'product_name': inventory_item.product_name,
                    'quantity': inventory_item.quantity,
                    'status': 'created' if created else 'updated'
                })
            except Exception as e:
                return Response({'status': 'error', 'message': str(e)}, status=400)
        return Response(response_data, status=201)

class JarCountViewSet(viewsets.ModelViewSet):
    queryset = JarCount.objects.all()
    serializer_class = JarCountSerializer
    pagination_class = pagination.PageNumberPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        date = self.request.query_params.get('date')
        if date:
            date = parse_date(date)
            if date:
                queryset = queryset.filter(timestamp__date=date)
        return queryset

    @action(detail=False, methods=['get'])
    def aggregate(self, request):
        date = request.query_params.get('date')
        if date:
            date = parse_date(date)
            if date:
                queryset = JarCount.objects.filter(timestamp__date=date)
                aggregation = queryset.values('shift').annotate(total=Sum('count')).order_by('shift')
                result = {
                    'shift1': next((item['total'] for item in aggregation if item['shift'] == 'day'), 0),
                    'shift2': next((item['total'] for item in aggregation if item['shift'] == 'night'), 0),
                    'total': sum(item['total'] for item in aggregation)
                }
                return Response(result)
        return Response({'error': 'Invalid or missing date'}, status=400)

    @action(detail=False, methods=['post'])
    def update_inventory(self, request):
        try:
            count = int(request.data.get('count'))
            shift = request.data.get('shift')
            inventory_id = request.data.get('inventory_id')

            inventory = Inventory.objects.get(id=inventory_id)

            depletion_rates = {
                'Jars': 1,
                'Lids': 1,
                'Labels': 1,
                'Sugar': 0.077,
                'Salt': 0.011,
                'Soy': 0.031,
                'Peanuts': 1.173,
                'Boxes': 1/12
            }

            required_quantity = count * depletion_rates[inventory.product_name]
            if inventory.quantity < required_quantity:
                return Response({'status': 'error', 'message': f'Insufficient {inventory.product_name}'})

            inventory.quantity -= required_quantity
            inventory.save()

            jar_count = JarCount.objects.create(inventory=inventory, count=count, shift=shift)

            return Response({'status': 'success', 'message': 'Inventory updated and jars counted'})
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def update_jar_count(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            jar_count = data.get('jar_count')
            shift = data.get('shift')
            timestamp = data.get('timestamp')

            if timestamp:
                central = pytz.timezone('America/Chicago')
                timestamp = datetime.fromisoformat(timestamp)
                if timestamp.tzinfo is None:
                    timestamp = make_aware(timestamp, timezone=central)
                else:
                    timestamp = timestamp.astimezone(central)

            depletion_rates = {
                'Jars': 1,
                'Lids': 1,
                'Labels': 1,
                'Sugar': 0.077,
                'Salt': 0.011,
                'Soy': 0.031,
                'Peanuts': 1.173,
                'Boxes': 1/12
            }

            if jar_count is not None and shift:
                for item, rate in depletion_rates.items():
                    inventory_item, created = Inventory.objects.get_or_create(product_name=item, defaults={'quantity': 0})
                    inventory_item.quantity -= jar_count * rate
                    inventory_item.save()

                jar_count_instance = JarCount.objects.create(
                    count=jar_count,
                    shift=shift,
                    timestamp=timezone.now()
                )

                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'fail', 'reason': 'Invalid data'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'fail', 'reason': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'fail', 'reason': str(e)}, status=400)
    elif request.method == 'GET':
        return JsonResponse({'status': 'info', 'message': 'Use POST to update jar count'}, status=200)
    else:
        return JsonResponse({'status': 'fail', 'reason': 'Invalid request method'}, status=405)

