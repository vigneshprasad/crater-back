from rest_framework import serializers

from users import models as user_models
from wn_analytics import models
from tags import serializers as tag_serializers
from conversations import services as conversation_services
from resources.meetings import services as meeting_services


class UserTraitsSerializer(serializers.ModelSerializer):
    """These parameters are sent to segment for tracking."""
    work_city = serializers.SerializerMethodField()
    social_auth = serializers.SerializerMethodField()
    user_tags = serializers.SerializerMethodField()
    twitter = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    user_objectives = serializers.SerializerMethodField(read_only=True)
    utm_source = serializers.SerializerMethodField(read_only=True)
    utm_campaign = serializers.SerializerMethodField(read_only=True)
    linkedin = serializers.CharField(
        source="profile.linkedin_url",
        read_only=True
    )
    years_of_experience = serializers.SerializerMethodField(read_only=True)
    sector = serializers.SerializerMethodField(read_only=True)
    education_level = serializers.SerializerMethodField(read_only=True)
    company_type = serializers.SerializerMethodField(read_only=True)
    last_meeting_date = serializers.SerializerMethodField(read_only=True)
    last_conversation_date = serializers.SerializerMethodField(read_only=True)
    total_conversations = serializers.SerializerMethodField(read_only=True)
    total_meetings = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = user_models.User
        fields = (
            "name",
            "email",
            "role",
            "city",
            "work_city",
            "phone",
            "intent",
            "email_verified",
            "phone_number_verified",
            "social_auth",
            "referer",
            "user_tags",
            "twitter",
            "source",
            "user_objectives",
            "linkedin",
            "utm_source",
            "utm_campaign",
            "date_joined",
            "years_of_experience",
            "sector",
            "education_level",
            "company_type",
            "last_meeting_date",
            "last_conversation_date",
            "total_conversations",
            "total_meetings"
        )

    @staticmethod
    def get_city(user):
        if not user.city:
            return None
        return user.city.name

    @staticmethod
    def get_social_auth(user):
        if not user.socialaccount_set.all():
            return None
        return user.socialaccount_set.first().provider

    @staticmethod
    def get_work_city(user):
        if not (user.has_profile and user.profile.work_city):
            return None
        return user.profile.work_city.name

    @staticmethod
    def get_utm_source(user):
        source = models.UserSource.objects.filter(user=user).last()
        if not source:
            return None
        return source.utm_source

    @staticmethod
    def get_utm_campaign(user):
        source = models.UserSource.objects.filter(user=user).last()
        if not source:
            return None
        return source.utm_campaign

    @staticmethod
    def get_user_tags(user):
        if not user.has_profile:
            return None
        user_tags = tag_serializers.TagSerializer(
            user.profile.tags,
            many=True,
            read_only=True
        ).data
        return ", ".join([tag["name"] for tag in user_tags])

    @staticmethod
    def get_twitter(user):
        if not user.has_profile:
            return None
        return user.profile.twitter

    @staticmethod
    def get_phone(user):
        return str(user.phone_number)

    @staticmethod
    def get_user_objectives(user):
        if not user.objectives.all():
            return None
        return ", ".join(
            [objective.name for objective in user.objectives.all()]
        )

    @staticmethod
    def get_years_of_experience(user):
        if not user.has_profile:
            return None
        profile = user.profile
        years_of_experience = profile.years_of_experience
        years_of_experience_str = dict(user_models.Profile.YEARS_OF_EXPERIENCE_CHOICES)[
            years_of_experience] if years_of_experience else None
        return years_of_experience_str

    @staticmethod
    def get_sector(user):
        if not user.has_profile:
            return None
        profile = user.profile
        sector = profile.sector
        sector_str = dict(user_models.Profile.SECTOR_CHOICES)[
            sector] if sector else None
        return sector_str

    @staticmethod
    def get_education_level(user):
        if not user.has_profile:
            return None
        profile = user.profile
        education_level = profile.education_level
        education_level_str = dict(user_models.Profile.YEARS_OF_EXPERIENCE_CHOICES)[
            education_level] if education_level else None
        return education_level_str

    @staticmethod
    def get_company_type(user):
        if not user.has_profile:
            return None
        profile = user.profile
        company_type = profile.company_type
        company_type_str = dict(user_models.Profile.YEARS_OF_EXPERIENCE_CHOICES)[
            company_type] if company_type else None
        return company_type_str

    @staticmethod
    def get_total_conversations(user):
        user_groups = conversation_services.get_groups_attended_for_user(user)
        return user_groups.count()

    @staticmethod
    def get_total_meetings(user):
        user_meetings = meeting_services.get_meetings_attended(user)
        return user_meetings.count()

    @staticmethod
    def get_last_conversation_date(user):
        latest_user_group = conversation_services.get_groups_attended_for_user(user).first()
        return latest_user_group.local_start if latest_user_group else None

    @staticmethod
    def get_last_meeting_date(user):
        latest_user_meeting = meeting_services.get_meetings_attended(user).first()
        return latest_user_meeting.local_start if latest_user_meeting else None
