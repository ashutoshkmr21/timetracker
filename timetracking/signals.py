from django.dispatch import Signal

timesheet_signal = Signal(providing_args=['user','project'])




