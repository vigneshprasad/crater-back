import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import status

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from conversations import constants as conversation_constants
from conversations import private as conversation_private
from conversations.dashboard import constants
from crater.creator import private as creator_private
from users import permissions as user_permissions
from users import public as user_public


class UserCreateSearchViewSet(viewsets.GenericViewSet):

    permission_classes = [user_permissions.AllowAny]

    @action(
        methods=["get"],
        queryset=get_user_model().objects.values(
            "pk", "name", "email", "phone_number"
        ),
        detail=False,
        permission_classes=[user_permissions.AllowAny]
    )
    def search(self, request):
        """Searches a users based on name, email and phone number.

        Note:
            It's return only the name, phone_number, email for the user.

        """
        search_text = request.query_params.get("s")
        queryset = self.get_queryset()

        result_queryset = queryset.filter(
            Q(name__icontains=search_text) |
            Q(email__icontains=search_text) |
            Q(username__icontains=search_text)
        )

        return Response(result_queryset, status=status.HTTP_200_OK)

    @staticmethod
    def create(request, *arg, **kwargs):
        """Creates a user for given parameters."""
        post_data = request.data
        name = post_data.get("name")
        phone_number = post_data.get("phone_number")
        email = post_data.get("email")
        primary_url = post_data.get("primary_url")

        phone_number_exists = False
        email_exists = False
        user = None

        try:
            user = user_public.get_user_for_phone_number(phone_number=phone_number)
        except Exception:
            phone_number_exists = True
        phone_number_exists = True if user else phone_number_exists

        try:
            user = user_public.get_user_for_email(email=email)
        except Exception:
            email_exists = True
        email_exists = True if user else email_exists

        if phone_number_exists and email_exists:
            return Response(
                {
                    "message": "Email and Phone Number already exists"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        elif phone_number_exists:
            return Response(
                {
                    "message": "Phone Number already exists"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        elif email_exists:
            return Response(
                {
                    "message": "Email already exists"
                }, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = user_public.create_user(
                phone_number=phone_number,
                email=email,
                name=name,
                primary_url=primary_url
            )
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        data = {
            "pk": user.pk,
            "phone_number": phone_number,
            "email": user.email,
            "name": user.display_name
        }

        return Response(data, status=status.HTTP_201_CREATED)


class CreateUpdateWebinarViewSet(viewsets.GenericViewSet):

    permission_classes = [user_permissions.AllowAny]

    @staticmethod
    def create(request, *args, **kwargs):
        """Searches a users based on name, email and phone number.

        Note:
            It's return only the name, phone_number, email for the user.

        """
        post_data = request.data
        host_id = post_data.get("host")
        # Get user object for host_id.
        try:
            host = get_user_model().objects.get(pk=host_id)
        except get_user_model().DoesNotExist:
            return Response(
                {
                    "message": "Invalid Host PK"
                }, status=status.HTTP_400_BAD_REQUEST
            )

        # List of speaker ids.
        speakers_ids = post_data.get("speakers", [])
        # Add host to speakers as well.
        speakers_ids.append(host_id)
        speakers = get_user_model().objects.filter(pk__in=speakers_ids)

        topic_id = post_data.get("topic")
        topic_details = post_data.get("topic_details")
        description = post_data.get("description")

        # Get category list of the stream.
        category_ids = post_data.get("categories")
        categories = []
        for category_id in category_ids:
            category = conversation_private.get_category_for_id(category_id)
            if not category:
                continue
            categories.append(category)

        # Sanitize start datetime for the stream.
        start_datetime = post_data.get("start")
        try:
            start = datetime.datetime.strptime(start_datetime, constants.RETOOL_DATETIME_FORMAT)
        except ValueError:
            return Response({
                "message": "Invalid Datetime format"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get display keys values.
        published = post_data.get("published", True)
        closed = post_data.get("closed", False)
        featured = post_data.get("featured", False)

        # Creator poc and prospector.
        creator_poc_id = post_data.get("creator_poc")
        creator_prospector_id = post_data.get("creator_prospector")

        # Create or get topic.
        if not topic_id:
            title = topic_details.get("title")
            image_name = topic_details.get("image")
            image_url = settings.AWS_DEFAULT_OBJECT_URL + "/media/{}".format(image_name)
            description = topic_details.get("description") or description
            topic_type = conversation_constants.GROUP_TYPE_WEBINAR_ENUM
            topic = conversation_private.create_topic(
                title,
                image_name=image_name,
                image_url=image_url,
                description=description,
                topic_type=topic_type
            )
        else:
            topic = conversation_private.get_topic(topic_id)

        # Get or create creator object for the host.
        creator = creator_private.get_or_create_creator(host)
        # Update creator object for host.
        if not creator.point_of_contact and creator_poc_id:
            creator.point_of_contact_id = creator_poc_id
        if not creator.prospector and creator_prospector_id:
            creator.prospector_id = creator_prospector_id

        creator.save()

        # Create stream.
        group = conversation_private.create_webinar(
            host=host,
            speakers=speakers,
            topic=topic,
            description=description,
            start=start,
            categories=categories,
            is_featured=featured,
            is_closed=closed,
            is_published=published
        )

        return Response({
            "id": group.id
        }, status=status.HTTP_200_OK)


class CategoryViewSet(viewsets.GenericViewSet):

    queryset = conversation_private.get_all_categories()
    permission_classes = [user_permissions.AllowAny]

    def list(self, request):
        """Return a list of category id and name"""
        data = [
            {"id": category.id, "name": category.name}
            for category in self.get_queryset()
        ]
        return Response(data, status=status.HTTP_200_OK)
