from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AccessHistory, Entitlement, Product, PurchaseHistory, User
from .permissions import IsSupportWriteOrReadOnly
from .serializers import (
    AccessHistorySerializer,
    EntitlementSerializer,
    LoginSerializer,
    ProductSerializer,
    PurchaseHistorySerializer,
    UserSerializer,
)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'role': user.role, 'user_id': user.id})


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer

    @action(detail=True, methods=['get'])
    def rights(self, request, pk=None):
        user = self.get_object()
        today = timezone.now().date()
        rights = Entitlement.objects.filter(user=user, is_revoked=False, end_date__gte=today)
        AccessHistory.objects.create(user=request.user, page=f'/users/{user.id}/rights')
        serializer = EntitlementSerializer(rights, many=True)
        return Response({'user': UserSerializer(user).data, 'active_rights': serializer.data})


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all().order_by('id')
    serializer_class = ProductSerializer


class EntitlementViewSet(viewsets.ModelViewSet):
    queryset = Entitlement.objects.select_related('user', 'product').all().order_by('-id')
    serializer_class = EntitlementSerializer
    permission_classes = [IsSupportWriteOrReadOnly]

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        entitlement = self.get_object()
        entitlement.is_revoked = True
        entitlement.revoked_at = timezone.now()
        entitlement.save()
        return Response({'status': 'revoked'}, status=status.HTTP_200_OK)


class PurchaseHistoryListView(generics.ListAPIView):
    queryset = PurchaseHistory.objects.select_related('user', 'product').all().order_by('-created_at')
    serializer_class = PurchaseHistorySerializer


class AccessHistoryListView(generics.ListAPIView):
    queryset = AccessHistory.objects.select_related('user').all().order_by('-accessed_at')
    serializer_class = AccessHistorySerializer
