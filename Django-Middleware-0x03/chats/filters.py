import django_filters
from .models import Message
from django.utils import timezone
from datetime import timedelta


class MessageFilter(django_filters.FilterSet):
    sender = django_filters.UUIDFilter(field_name='sender__user_id')
    after = django_filters.DateTimeFilter(field_name='sent_at', lookup_expr='gte')
    before = django_filters.DateTimeFilter(field_name='sent_at', lookup_expr='lte')

    class Meta:
        model = Message
        fields = ['sender', 'after', 'before']