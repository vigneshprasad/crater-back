from django.utils.translation import ugettext_lazy as _

REASON_CHOICES = (
    ('18_year_old', _('I am atleast 18 year old.')),
    ('join', _('I want to join the community to collaborate or share.')),
    ('understand', _('I understand the membership appication process.')),
    ('can_verify_bank_account', _('I can verify a bank acoount & government-issued ID')),
    ('have_a_debit', _('I have a debit &/ or credit card')),
    ('investor_in_companies', _('I am qualified to sign up as an investor in companies')),
    (
        'connectionsare',
        _('I understand that no from of trading of equities take place on the platform, only connectionsare made')
    )
)
