from django.dispatch import Signal

upload_received = Signal(providing_args = ['guid', 'data'])