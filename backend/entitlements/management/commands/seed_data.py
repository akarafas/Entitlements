from django.core.management.base import BaseCommand
from entitlements.models import Product, User


class Command(BaseCommand):
    help = 'Seed products and test users'

    def handle(self, *args, **options):
        Product.objects.get_or_create(name='Digital Basic', access_type='digital')
        Product.objects.get_or_create(name='Print Weekly', access_type='print')
        Product.objects.get_or_create(name='Premium All-Access', access_type='premium')

        support_defaults = {
            'username': 'support',
            'first_name': 'Support',
            'last_name': 'Agent',
            'address': '123 Support Street',
            'role': 'support',
        }
        developer_defaults = {
            'username': 'developer',
            'first_name': 'Dev',
            'last_name': 'Reader',
            'address': '456 Developer Avenue',
            'role': 'developer',
        }

        support, created = User.objects.get_or_create(email='support@example.com', defaults=support_defaults)
        if created:
            support.set_password('Support123!')
            support.save()

        dev, created = User.objects.get_or_create(email='developer@example.com', defaults=developer_defaults)
        if created:
            dev.set_password('Developer123!')
            dev.save()

        self.stdout.write(self.style.SUCCESS('Seed data ensured.'))
