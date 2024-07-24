from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InventoryViewSet, JarCountViewSet, ShiftTimingViewSet, update_jar_count

router = DefaultRouter()
router.register(r'inventories', InventoryViewSet)
router.register(r'jarcounts', JarCountViewSet)
router.register(r'shifttimings', ShiftTimingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('update_jar_count/', update_jar_count, name='update_jar_count'),
]
