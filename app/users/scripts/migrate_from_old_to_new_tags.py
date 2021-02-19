from users import models
from tags import models as tag_models


TAGS_TO_NEW_TAGS_MATCH = {
    "Accountant": "Financial Experts",
    "Associate": "Other",
    "Board Member": "Senior Executives",
    "Brand Advisor": "Marketing Experts",
    "Business Advisor": "Business Advisors",
    "Business Development Executive": "Business Development Executives",
    "Business Owner (SME)": "SME Owners",
    "Business Specialist": "Business Advisors",
    "CEO": "Startup Founders",
    "CFA": "Financial Experts",
    "CFO": "Senior Executives",
    "COO": "Senior Executives",
    "CTO": "Startup Founders",
    "Company Secretary": "Financial Experts",
    "Consultant": "Business Advisor",
    "Designer": "Designers",
    "Director": "Senior Executives",
    "Engineer": "Engineers",
    "Entrepreneur": "SME Owners",
    "Finance Specialist": "Financial Experts",
    "Financial Advisor": "Financial Experts",
    "Financial Analyst": "Financial Experts",
    "Financial Expert": "Financial Experts",
    "Graphic Designer": "Designers",
    "Growth Hacker": "Marketing Experts",
    "Influencer": "Marketing Experts",
    "Investment fund": "Startup Investors",
    "Investor": "Startup Investors",
    "Journalist": "Marketing Expert",
    "Lawyer": "Lawyers",
    "Manager": "Business Development Executives",
    "Marketing Agency": "Marketing Experts",
    "Marketing Expert": "Marketing Experts",
    "Other": "Others",
    "Partner": "Senior Executives",
    "President": "Senior Executives",
    "Principal": "Senior Executives",
    "Product Manager": "Product Managers",
    "Professional": "Others",
    "Senior Executives": "Senior Executives",
    "Startup": "Startup Founders",
    "Startup Founder": "Startup Founders",
    "Startup Investor": "Startup Investors",
    "Students or Intern": "Student or Intern",
    "Thought Leader": "Senior Executives",
    "UI/UX Designer": "Designers",
    "Vice President": "Senior Executives",
    "Videographer": "Designers",
    "Writer": "Marketing Experts"
}


def migrate_tags_to_new_tag(users=None):
    """Migrate users with old tags and create a single new tag."""

    all_users = users if users else models.User.objects.all()

    for user in all_users:
        if not user.has_profile:
            continue

        profile = user.profile
        all_tags = profile.tags.all().values_list("name", flat=True)
        primary_tag = all_tags[0] if all_tags else "Others"
        new_tag = TAGS_TO_NEW_TAGS_MATCH.get(primary_tag, "Others")
        new_tag_obj, _ = tag_models.Tag.objects.get_or_create(name=new_tag)
        # profile.tags.clear()
        profile.new_tag.add(new_tag_obj)
