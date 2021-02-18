TAGS_TO_NEW_TAGS_MATCH = {
    "Engineer": "Engineers",
    "Designers": "Designers",
    "Business Development Executive": "Business Development Executives",
    "Business Advisors": "Business Advisors",
    "Business Owner (SME)": "SME Owners",
    "Senior Executives": "Senior Executives",
    "Financial Expert": "Financial Experts",
    "Lawyer": "Lawyers",
    "Marketing experts": "Marketing Experts",
    "Product Manager": "Product Managers",
    "Startup Investor": "Startup Investors",
    "Startup Founder": "Startup Founders",
    "Students or Intern": "Student or Intern",
    "Brand Advisor": "Marketing Experts",
    "Business Specialist": "Business Advisors",
    "Finance Specialist": "Financial Experts",
    "Financial Advisor": "Financial Experts",
    "Financial Analyst": "Financial Experts",
    "CFA": "Financial Experts",
    "Company Secretary": "Financial Experts",
    "Graphic Designer": "Designers",
    "Growth Hacker": "Marketing Experts",
    "Influencer": "Marketing Experts",
    "Investment fund": "Startup Investors",
    "Investor": "Startup Investors",
    "Marketing Agency": "Marketing Experts",
    "UI/UX Designer": "Designers",
    "Accountant": "Financial Experts",
    "CEO": "Startup Founders",
    "CFO": "Senior Executives",
    "COO": "Senior Executives",
    "CTO": "Startup Founders",
    "Director": "Senior Executives",
    "Board Member": "Senior Executives",
    "Entrepreneur": "SME Owners",
    "Partner": "Senior Executives",
    "Principal": "Senior Executives",
    "Vice President": "Senior Executives",
    "Startup": "Startup Founders",
    "Associate": "Other",
    "Consultant": "Business Advisor",
    "Journalist": "Marketing Expert",
    "Manager": "Business Development Executives",
    "Other": "Others",
    "Professional": "Others",
    "Thought Leader": "Senior Executives",
    "Videographer": "Designers",
    "Writer": "Marketing Experts"
}

from users import models
from tags import models as tag_models


def make_old_tags_inactive():
    tag_names = TAGS_TO_NEW_TAGS_MATCH.keys()
    tag_models.Tag.objects.filter(name__in=tag_names).update(is_active=False)


def migrate_to_new_tags():
    for user in models.User.objects.all():
        if not user.has_profile:
            continue
        profile = user.profile
        all_tags = profile.tags.all().values_list("name", flat=True)
        primary_tag = all_tags[0] if all_tags else "Others"
        new_tag = TAGS_TO_NEW_TAGS_MATCH.get(primary_tag, "Others")
        new_tag_obj, _ = tag_models.Tag.objects.get_or_create(name=new_tag)
        profile.tags.clear()
        profile.tags.add(new_tag_obj)
