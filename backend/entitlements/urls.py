from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AccessHistoryListView,
    EntitlementViewSet,
    LoginView,
    ProductViewSet,
    PurchaseHistoryListView,
    UserViewSet,
)

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('products', ProductViewSet)
router.register('entitlements', EntitlementViewSet)

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('purchase-history/', PurchaseHistoryListView.as_view(), name='purchase-history'),
    path('access-history/', AccessHistoryListView.as_view(), name='access-history'),
    path('', include(router.urls)),
]
