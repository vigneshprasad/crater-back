from django.conf import settings
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class BuildVersionView(RetrieveAPIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response(settings.BUILD_VERSION or 1)
