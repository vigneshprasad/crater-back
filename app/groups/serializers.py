from rest_framework import serializers

from groups import models


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Category


class AgendaSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Agenda


class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Group


class InviteSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Invite


class RequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Request
