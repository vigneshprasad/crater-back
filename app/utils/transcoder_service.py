import uuid
import boto3

from botocore import exceptions as botocore_exceptions
from django.conf import settings

from users import models


class TranscoderService:

    def __init__(self, pipeline_id, aws_access_key_id=None, aws_secret_access_key=None, region_name="eu-west-1"):

        self.etc_client = boto3.client(
            "elastictranscoder",
            region_name=region_name,
            **{
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key
            }
            if aws_access_key_id else {}
        )
        self.pipeline_id = pipeline_id
        self.presets = {
            "mp4": settings.MP4_TRANSCODER_PRESET_ID
        }
        self.output_file_prefix = "elastic-transcoder/output/"

    def create_transcoder_job(self, profile_pk):

        try:
            profile = models.Profile.objects.get(pk=profile_pk)
        except models.Profile.DoesNotExist:
            return None, None

        if profile.cover and profile.cover.url != profile._old_cover:
            return None, None

        cover_name = profile.cover.name
        ext = cover_name.split(".")[1]
        if ext.lower() not in ["mov", "mpeg", "avi", "mp4", "3gp", "mwv", "flv"]:
            return None, None

        input_file = f"media/{cover_name}"
        output_file = str(uuid.uuid4())
        while models.Profile.objects.filter(transcoder_uuid=output_file).exists():
            output_file = str(uuid.uuid4())

        outputs = [
            {
                "Key": f"mp4/{output_file}.mp4",
                "PresetId": self.presets.get("mp4"),
                "ThumbnailPattern": f"thumbnail/{output_file}"+"-{count}",
            },
        ]
        job_info = self.create_elastic_transcoder_hls_job(
            input_file=input_file, outputs=outputs, output_file_prefix=self.output_file_prefix
        )
        print(job_info)
        if job_info:
            return job_info["Id"], output_file

        return None, None

    def create_file_transcoder_job(self, cover_file_pk):

        try:
            cover_file = models.CoverFile.objects.get(pk=cover_file_pk)
        except models.CoverFile.DoesNotExist:
            return None, None
        cover_name = cover_file.file.name
        ext = cover_name.split(".")[-1]
        if ext.lower() not in ["mov", "mpeg", "avi", "mp4", "3gp", "mwv", "flv"]:
            return None, None

        input_file = f"media/{cover_name}"
        output_file = str(uuid.uuid4())
        while models.CoverFile.objects.filter(transcoder_uuid=output_file).exists():
            output_file = str(uuid.uuid4())

        outputs = [
            {
                "Key": f"mp4/{output_file}.mp4",
                "PresetId": self.presets.get("mp4"),
                "ThumbnailPattern": f"thumbnail/{output_file}"+"-{count}",
            },
        ]
        job_info = self.create_elastic_transcoder_hls_job(
            input_file=input_file, outputs=outputs, output_file_prefix=self.output_file_prefix
        )
        print(job_info)
        if job_info:
            return job_info["Id"], output_file

        return None, None

    def create_elastic_transcoder_hls_job(
            self,
            input_file,
            outputs,
            output_file_prefix
    ):
        """Create an Elastic Transcoder job

            # :param pipeline_id: string; ID of an existing Elastic Transcoder pipeline
            :param input_file: string; Name of existing object in pipeline's S3 input bucket
            :param outputs: list of dictionaries; Parameters defining each output file
            :param output_file_prefix: string; Prefix for each output file name

            :return Dictionary containing information about the job
                If job could not be created, returns None
        """

        try:
            response = self.etc_client.create_job(
                PipelineId=self.pipeline_id,
                Input={"Key": input_file},
                Outputs=outputs,
                OutputKeyPrefix=output_file_prefix,
                Playlists=[]
            )
        except botocore_exceptions.ClientError as e:
            print(f"ERROR: {e}")
            return None
        return response["Job"]

    def job_success(self, job_id):
        try:
            job = self.etc_client.read_job(Id=job_id)["Job"]
        except (botocore_exceptions.ClientError, botocore_exceptions.NoCredentialsError) as e:
            print(f"ERROR: {e}")
            return False

        if job["Status"] == "Complete":
            return True

        return False


if getattr(settings, "AWS_ACCESS_KEY_ID") and getattr(settings, "AWS_TRANSCODER_REGION_NAME"):
    transcoder_service = TranscoderService(
        pipeline_id=settings.MP4_PIPELINE_ID,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_TRANSCODER_REGION_NAME
    )
else:
    transcoder_service = TranscoderService(
        pipeline_id=settings.MP4_PIPELINE_ID,
        region_name=settings.AWS_TRANSCODER_REGION_NAME
    )
