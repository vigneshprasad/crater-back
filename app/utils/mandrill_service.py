# from mandrill import Mandrill
# from django.conf import settings
#
# class MandrillService:
#
#     def __init__(self, api_key):
#         self.client = Mandrill(api_key)
#         self.template_names = {
#             'password_reset': 'Password Reset'
#         }
#
#     def send_email(
#             self,
#             template_name: str,
#             content: dict,
#             to: list,
#             from_: str = settings.DEFAULT_EMAIL_FROM,
#             from_name: str = 'Example name'
#         ):
#         '''
#         Send email method
#         Examle:
#         "to": [
#             {
#                 "email": "example@email.com",
#                 "name": "Recipient Name",
#                 "type": "to"
#             }
#         ]
#         '''
#         message = {
#             'from_name': from_name,
#             'from_email': from_,
#             'to': to
#         }
#         self.client.messages.send_template(
#             template_name=self.template_names.get(template_name),
#             template_content=content,
#             message=message
#         )
#
#
# mandrill_service = MandrillService(api_key=settings.MANDRILL_API_KEY)
