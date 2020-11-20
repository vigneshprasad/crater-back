from django.dispatch import Signal

package_request_created = Signal(providing_args=[
    "user",
    "points_applied",
])
