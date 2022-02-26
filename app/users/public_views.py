from django.db import transaction
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from resources.meetings import signals
from services import serializers as service_serializers
from users import permissions
from users import models
from users import constants
from users.paginators import Pagination
from users.scripts.create_users_from_csv import create_user_and_profile


class TypeFormViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):

    def create(self, request, *args, **kwargs):
        """Creates a user and meeting preference for a typeform entry."""

        form = request.data["form_response"]
        fields = form["definition"]["fields"]
        answers = form["answers"]
        typeform_url = "https://worknetwork.typeform.com/to/" + form["form_id"]
        try:
            new_source = models.Source.objects.get(link=typeform_url)
        except models.Source.DoesNotExist:
            new_source = None

        user = {
            "email": form.get("hidden").get("email") if form.get("hidden") else None,
            "phone_number": None,
            "interests": [],
            "time_preferences": [],
            "meeting_days": [],
            "tags": [],
            "utm_source": form.get("hidden").get("utm_source") if form.get("hidden") else None,
            "utm_campaign": form.get("hidden").get("utm_campaign") if form.get("hidden") else None,
            "source": constants.TYPEFORM_URL_TO_SOURCE_MAP.get(typeform_url) or typeform_url,
            "new_source": new_source,
            "objectives": [],
            "years_of_experience": None,
            "company_type": None,
            "education_level": None,
            "sector": None,
            "linkedin_url": None
        }

        for i in range(len(fields)):
            if fields[i]["ref"] == "full_name":
                user["name"] = answers[i]["text"]
            elif fields[i]["ref"] == "email":
                user["email"] = answers[i]["email"]
            elif fields[i]["ref"] == "phone_number":
                user["phone_number"] = answers[i]["phone_number"]
            elif fields[i]["ref"] == "years_of_experience":
                user["years_of_experience"] = answers[i]["choice"]["label"].strip()
            elif fields[i]["ref"] == "company_type":
                user["company_type"] = answers[i]["choice"]["label"].strip()
            elif fields[i]["ref"] == "education_level":
                user["education_level"] = answers[i]["choice"]["label"].strip()
            elif fields[i]["ref"] == "sector":
                user["sector"] = answers[i]["choice"]["label"].strip()
            elif fields[i]["ref"] == "meeting_days":
                days = answers[i]["choice"]["label"]
                if days == "Both work":
                    user["meeting_days"].append("Thursday")
                    user["meeting_days"].append("Friday")
                else:
                    user["meeting_days"].append(days)
            elif fields[i]["ref"] == "linkedin_url":
                user["linkedin_url"] = answers[i]["url"]
            # Objectives looking for.
            elif fields[i]["ref"] == "objective_looking_for" and fields[i].get("allow_multiple_selections", False):
                for objective_for in answers[i]["choices"]["labels"]:
                    user["objectives"].append(objective_for)
            elif fields[i]["ref"] == "objective_looking_for":
                user["objectives"].append(answers[i]["choice"]["label"])
            # Objectives looking to.
            elif fields[i]["ref"] == "objective_looking_to" and fields[i].get("allow_multiple_selections", False):
                for objective_to in answers[i]["choices"]["labels"]:
                    user["objectives"].append(objective_to)
            elif fields[i]["ref"] == "objective_looking_to":
                user["objectives"].append(answers[i]["choice"]["label"])
            elif fields[i]["ref"] == "interests" and fields[i].get("allow_multiple_selections", False):
                for interest in answers[i]["choices"]["labels"]:
                    user["interests"].append(interest)
            elif fields[i]["ref"] == "interests":
                user["interests"].append(answers[i]["choice"]["label"])
            elif fields[i]["ref"] == "tags" and fields[i].get("allow_multiple_selections", False):
                for tag in answers[i]["choices"]["labels"]:
                    user["tags"].append(tag)
            elif fields[i]["ref"] == "tags":
                user["tags"].append(answers[i]["choice"]["label"])
            elif fields[i]["ref"] == "time_preferences" and fields[i].get("allow_multiple_selections", False):
                for preference in answers[i]["choices"]["labels"]:
                    user["time_preferences"].append(preference)
            elif fields[i]["ref"] == "time_preferences":
                user["time_preferences"].append(answers[i]["choice"]["label"])

        if not user["email"]:
            return Response({"status": "No email exists"})

        # This code will run under a single transaction in the DB. Avoiding
        # creation of multiple preferences for user.
        with transaction.atomic():

            user_obj, _ = create_user_and_profile(
                full_name=user["name"],
                email=user["email"],
                phone_number=user["phone_number"],
                linkedin_url=user["linkedin_url"],
                tags=user["tags"],
                source=user["source"],
                new_source=user["new_source"],
                utm_source=user["utm_source"],
                utm_campaign=user["utm_campaign"],
                years_of_experience=user["years_of_experience"],
                company_type=user["company_type"],
                education_level=user["education_level"],
                sector=user["sector"]
            )

            if not user["meeting_days"]:
                user["meeting_days"] = ["Thursday", "Friday"]

            signals.create_new_meeting_preference_typeform.send(
                sender=None,
                user=user_obj,
                objectives=user["objectives"],
                time_preferences=user["time_preferences"],
                interests=user["interests"],
                days=user["meeting_days"]
            )

        return Response({"status": "Success"})
