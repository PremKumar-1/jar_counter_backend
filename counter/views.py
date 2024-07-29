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

from rest_framework import viewsets, pagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils.dateparse import parse_date
from django.db.models import Sum, Q
from datetime import datetime, timedelta
from .models import JarCount, Inventory
from .serializers import JarCountSerializer, InventorySerializer
import logging
from .pagination import RelativeUrlPagination
import pytz
from django.utils import timezone

logger = logging.getLogger(__name__)

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
                logger.error(f"Error updating/creating inventory: {str(e)}")
                return Response({'status': 'error', 'message': str(e)}, status=400)
        return Response(response_data, status=201)

class JarCountViewSet(viewsets.ModelViewSet):
    queryset = JarCount.objects.all()
    serializer_class = JarCountSerializer
    pagination_class = RelativeUrlPagination

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            date = self.request.query_params.get('date')
            if date:
                date = parse_date(date)
                if date:
                    start_of_day_shift = datetime.combine(date, datetime.min.time()) + timedelta(hours=8)
                    end_of_day_shift = start_of_day_shift + timedelta(hours=12)
                    start_of_night_shift = end_of_day_shift
                    end_of_night_shift = start_of_day_shift + timedelta(hours=24)

                    queryset = queryset.filter(
                        (Q(timestamp__gte=start_of_day_shift) & Q(timestamp__lt=end_of_day_shift) & Q(shift='day')) |
                        (Q(timestamp__gte=start_of_night_shift) & Q(timestamp__lt=end_of_night_shift) & Q(shift='night'))
                    )
            return queryset
        except Exception as e:
            logger.error(f"Error in get_queryset: {str(e)}")
            raise e


    @action(detail=False, methods=['get'])
    def aggregate(self, request):
        try:
            date = request.query_params.get('date')
            if date:
                date = parse_date(date)
                if date:
                    start_of_day_shift = datetime.combine(date, datetime.min.time()) + timedelta(hours=8)
                    end_of_day_shift = start_of_day_shift + timedelta(hours=12)
                    start_of_night_shift = end_of_day_shift
                    end_of_night_shift = start_of_day_shift + timedelta(hours=24)

                    day_shift_aggregation = JarCount.objects.filter(
                        timestamp__gte=start_of_day_shift,
                        timestamp__lt=end_of_day_shift,
                        shift='day'
                    ).aggregate(total=Sum('count'))

                    night_shift_aggregation = JarCount.objects.filter(
                        timestamp__gte=start_of_night_shift,
                        timestamp__lt=end_of_night_shift,
                        shift='night'
                    ).aggregate(total=Sum('count'))

                    result = {
                        'shift1': day_shift_aggregation['total'] or 0,
                        'shift2': night_shift_aggregation['total'] or 0,
                        'total': (day_shift_aggregation['total'] or 0) + (night_shift_aggregation['total'] or 0)
                    }
                    return Response(result)
            return Response({'error': 'Invalid or missing date'}, status=400)
        except Exception as e:
            logger.error(f"Error in aggregate: {str(e)}")
            return Response({'error': str(e)}, status=500)

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
            logger.error(f"Error in update_inventory: {str(e)}")
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
            logger.error(f"Error in update_jar_count: {str(e)}")
            return JsonResponse({'status': 'fail', 'reason': str(e)}, status=400)
    elif request.method == 'GET':
        return JsonResponse({'status': 'info', 'message': 'Use POST to update jar count'}, status=200)
    else:
        return JsonResponse({'status': 'fail', 'reason': 'Invalid request method'}, status=405)
"""

from rest_framework import viewsets, pagination, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils.dateparse import parse_date
from django.db.models import Sum
from datetime import datetime, timedelta, time
from .models import JarCount, ShiftTiming, Inventory
from .serializers import JarCountSerializer, ShiftTimingSerializer, InventorySerializer
import logging
import pytz
from django.utils import timezone
from .pagination import RelativeUrlPagination
from django.db import transaction
from django.utils.timezone import make_aware

logger = logging.getLogger(__name__)

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
                logger.error(f"Error updating/creating inventory: {str(e)}")
                return Response({'status': 'error', 'message': str(e)}, status=400)
        return Response(response_data, status=201)

class JarCountViewSet(viewsets.ModelViewSet):
    queryset = JarCount.objects.all()
    serializer_class = JarCountSerializer
    pagination_class = RelativeUrlPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        date = self.request.query_params.get('date')
        if date:
            date = parse_date(date)
            if date:
                shift_timings = ShiftTiming.objects.first()
                if shift_timings:
                    shift1_start = make_aware(datetime.combine(date, shift_timings.shift1_start))
                    shift2_start = make_aware(datetime.combine(date, shift_timings.shift2_start))
                else:
                    shift1_start = make_aware(datetime.combine(date, time(8, 0)))
                    shift2_start = make_aware(datetime.combine(date, time(20, 0)))

                shift1_end = shift1_start + timedelta(hours=12)  # Assuming 12-hour shifts
                shift2_end = shift2_start + timedelta(hours=12)  # Assuming 12-hour shifts

                queryset = queryset.filter(
                    (Q(timestamp__gte=shift1_start) & Q(timestamp__lt=shift1_end)) |
                    (Q(timestamp__gte=shift2_start) & Q(timestamp__lt=shift2_end))
                ).order_by('timestamp')
        return queryset

    @action(detail=False, methods=['get'])
    def aggregate(self, request):
        date = request.query_params.get('date')
        if date:
            date = parse_date(date)
            if date:
                shift_timings = ShiftTiming.objects.first()
                if shift_timings:
                    shift1_start = datetime.combine(date, shift_timings.shift1_start)
                    shift2_start = datetime.combine(date, shift_timings.shift2_start)
                else:
                    shift1_start = datetime.combine(date, time(8, 0))
                    shift2_start = datetime.combine(date, time(20, 0))

                day_shift_aggregation = JarCount.objects.filter(
                    timestamp__gte=shift1_start,
                    timestamp__lt=shift2_start
                ).aggregate(total=Sum('count'))

                night_shift_aggregation = JarCount.objects.filter(
                    timestamp__gte=shift2_start,
                    timestamp__lt=shift1_start + timedelta(days=1)
                ).aggregate(total=Sum('count'))

                result = {
                    'shift1': day_shift_aggregation['total'] or 0,
                    'shift2': night_shift_aggregation['total'] or 0,
                    'total': (day_shift_aggregation['total'] or 0) + (night_shift_aggregation['total'] or 0)
                }
                return Response(result)
        return Response({'error': 'Invalid or missing date'}, status=status.HTTP_400_BAD_REQUEST)

class ShiftTimingViewSet(viewsets.ModelViewSet):
    queryset = ShiftTiming.objects.all()
    serializer_class = ShiftTimingSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

"""@csrf_exempt
def update_jar_count(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            jar_count = data.get('jar_count')
            timestamp = data.get('timestamp')

            if timestamp:
                central = pytz.timezone('America/Chicago')
                timestamp = datetime.fromisoformat(timestamp)
                if timestamp.tzinfo is None:
                    timestamp = timezone.make_aware(timestamp, timezone=central)
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

            if jar_count is not None:
                for item, rate in depletion_rates.items():
                    inventory_item, created = Inventory.objects.get_or_create(product_name=item, defaults={'quantity': 0})
                    inventory_item.quantity -= jar_count * rate
                    inventory_item.save()

                shift_timings = ShiftTiming.objects.first()
                if not shift_timings:
                    shift_timings = ShiftTiming.objects.create()

                JarCount.objects.create(
                    count=jar_count,
                    timestamp=timestamp,
                    shift1_start=shift_timings.shift1_start,
                    shift2_start=shift_timings.shift2_start
                )

                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'fail', 'reason': 'Invalid data'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'fail', 'reason': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error in update_jar_count: {str(e)}")
            return JsonResponse({'status': 'fail', 'reason': str(e)}, status=400)
    elif request.method == 'GET':
        return JsonResponse({'status': 'info', 'message': 'Use POST to update jar count'}, status=200)
    else:
        return JsonResponse({'status': 'fail', 'reason': 'Invalid request method'}, status=405)"""

@csrf_exempt
def update_jar_count(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            jar_count = data.get('jar_count')
            timestamp = data.get('timestamp')

            if not jar_count:
                return JsonResponse({'status': 'fail', 'reason': 'Invalid jar count'}, status=400)

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

            try:
                with transaction.atomic():
                    for item, rate in depletion_rates.items():
                        inventory_item = Inventory.objects.select_for_update().get(product_name=item)
                        original_quantity = inventory_item.quantity
                        inventory_item.quantity -= jar_count * rate
                        inventory_item.save()
                        logger.info(f"Updated {item}: {original_quantity} -> {inventory_item.quantity}")

                    shift_timings = ShiftTiming.objects.first()
                    if not shift_timings:
                        shift_timings = ShiftTiming.objects.create()

                    JarCount.objects.create(
                        count=jar_count,
                        timestamp=timestamp,
                        shift1_start=shift_timings.shift1_start,
                        shift2_start=shift_timings.shift2_start
                    )

                return JsonResponse({'status': 'success'})
            except Inventory.DoesNotExist:
                return JsonResponse({'status': 'fail', 'reason': 'Inventory item not found'}, status=400)
            except Exception as e:
                logger.error(f"Error in update_jar_count: {str(e)}")
                return JsonResponse({'status': 'fail', 'reason': str(e)}, status=400)

        except json.JSONDecodeError:
            logger.error("Invalid JSON")
            return JsonResponse({'status': 'fail', 'reason': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error in update_jar_count: {str(e)}")
            return JsonResponse({'status': 'fail', 'reason': str(e)}, status=400)
    elif request.method == 'GET':
        return JsonResponse({'status': 'info', 'message': 'Use POST to update jar count'}, status=200)
    else:
        return JsonResponse({'status': 'fail', 'reason': 'Invalid request method'}, status=405)