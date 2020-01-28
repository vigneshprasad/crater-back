import uuid

import boto3
from botocore.exceptions import ClientError
from django.conf import settings


class TranscoderService:
    def __init__(self, pipeline_id, aws_access_key_id, aws_secret_access_key, region_name='eu-west-1'):
        self.etc_client = boto3.client(
            'elastictranscoder',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        self.pipeline_id = pipeline_id
        self.presets = {
            # 'mp4': '1351620000001-000010'
            'mp4': settings.MP4_TRANSCODER_PRESET_ID
        }
        self.output_file_prefix = 'elastic-transcoder/output/'

    def create_transcoder_job(self, profile_pk):
        from users.models import Profile
        try:
            profile = Profile.objects.get(pk=profile_pk)
            if profile.cover and profile.cover.url != profile._old_cover:
                cover_name = profile.cover.name
                ext = cover_name.split('.')[1]
                if ext.lower() in ['mov', 'mpeg', 'avi', 'mp4', '3gp', 'mwv', 'flv']:
                    input_file = f'media/{cover_name}'
                    output_file = str(uuid.uuid4())
                    while Profile.objects.filter(transcoder_uuid=output_file).exists():
                        output_file = str(uuid.uuid4())
                    outputs = [
                        {
                            'Key': f'mp4/{output_file}.mp4',
                            'PresetId': self.presets.get('mp4'),
                            'ThumbnailPattern': f'thumbnail/{output_file}'+'-{count}',
                        },
                    ]
                    job_info = self.create_elastic_transcoder_hls_job(
                        input_file=input_file, outputs=outputs, output_file_prefix=self.output_file_prefix
                    )
                    print(job_info)
                    if job_info:
                        return job_info['Id'], output_file
            return None, None
        except Profile.DoesNotExist:
            return None, None

    def create_file_transcoder_job(self, cover_file_pk):
        from users.models import CoverFile
        try:
            cover_file = CoverFile.objects.get(pk=cover_file_pk)
            cover_name = cover_file.file.name
            ext = cover_name.split('.')[1]
            if ext.lower() in ['mov', 'mpeg', 'avi', 'mp4', '3gp', 'mwv', 'flv']:
                input_file = f'media/{cover_name}'
                output_file = str(uuid.uuid4())
                while CoverFile.objects.filter(transcoder_uuid=output_file).exists():
                    output_file = str(uuid.uuid4())
                outputs = [
                    {
                        'Key': f'mp4/{output_file}.mp4',
                        'PresetId': self.presets.get('mp4'),
                        'ThumbnailPattern': f'thumbnail/{output_file}'+'-{count}',
                    },
                ]
                job_info = self.create_elastic_transcoder_hls_job(
                    input_file=input_file, outputs=outputs, output_file_prefix=self.output_file_prefix
                )
                print(job_info)
                if job_info:
                    return job_info['Id'], output_file
            return None, None
        except CoverFile.DoesNotExist:
            return None, None

    def create_elastic_transcoder_hls_job(self,
                                          input_file,
                                          outputs,
                                          output_file_prefix,):
        """Create an Elastic Transcoder job

        :param pipeline_id: string; ID of an existing Elastic Transcoder pipeline
        :param input_file: string; Name of existing object in pipeline's S3 input bucket
        :param outputs: list of dictionaries; Parameters defining each output file
        :param output_file_prefix: string; Prefix for each output file name
        :return Dictionary containing information about the job
                If job could not be created, returns None
        """

        try:
            response = self.etc_client.create_job(PipelineId=self.pipeline_id,
                                                  Input={'Key': input_file},
                                                  Outputs=outputs,
                                                  OutputKeyPrefix=output_file_prefix,
                                                  Playlists=[])
        except ClientError as e:
            print(f'ERROR: {e}')
            return None
        return response['Job']

    def job_success(self, job_id):
        try:
            job = self.etc_client.read_job(Id=job_id)['Job']
            if job['Status'] == 'Complete':
                return True
        except ClientError as e:
            print(f'ERROR: {e}')
        return False


transcoder_service = TranscoderService(
    pipeline_id=settings.MP4_PIPELINE_ID,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name='eu-west-1'
)
