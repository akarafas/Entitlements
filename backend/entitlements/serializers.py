from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import AccessHistory, Entitlement, Product, PurchaseHistory, User, calculate_end_date


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['email'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials.')
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'username', 'email', 'address', 'role']

    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return (obj.get_full_name() or obj.username).strip()


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'access_type']


class EntitlementSerializer(serializers.ModelSerializer):
    length_days = serializers.IntegerField(write_only=True, min_value=1)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Entitlement
        fields = [
            'id', 'user', 'user_email', 'product', 'product_name',
            'start_date', 'end_date', 'length_days', 'is_revoked', 'revoked_at',
            'is_active', 'is_expired',
        ]
        read_only_fields = ['end_date', 'is_revoked', 'revoked_at']

    def create(self, validated_data):
        length_days = validated_data.pop('length_days')
        start_date = validated_data.get('start_date')
        validated_data['end_date'] = calculate_end_date(start_date, length_days)
        entitlement = super().create(validated_data)
        PurchaseHistory.objects.create(
            user=entitlement.user,
            product=entitlement.product,
            price=9.99,
            date_start=entitlement.start_date,
            date_end=entitlement.end_date,
        )
        return entitlement

    def update(self, instance, validated_data):
        length_days = validated_data.pop('length_days', None)
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.user = validated_data.get('user', instance.user)
        instance.product = validated_data.get('product', instance.product)
        if length_days:
            instance.end_date = calculate_end_date(instance.start_date, length_days)
        instance.save()
        return instance


class PurchaseHistorySerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = PurchaseHistory
        fields = '__all__'


class AccessHistorySerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = AccessHistory
        fields = '__all__'
