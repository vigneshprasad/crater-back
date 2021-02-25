from users import models
from tags import models as tag_models


TAGS_TO_CORRECTED_TAGS_MATCH = {
    "Accountant": "Financial Expert",
    "Associate": "Others",
    "HR Executives": "HR Executive",
    "Board Member": "Senior Executive",
    "Senior Executives": "Senior Executive",
    "Brand Advisor": "Marketing Expert",
    "Marketing Experts": "Marketing Expert",
    "Business Advisors": "Business Advisor",
    "Business Development Executives": "Business Development Executive",
    "Business Owner (SME)": "SME Owner",
    "SME Owners": "SME Owner",
    "Business Specialist": "Business Advisor",
    "CEO": "Startup Founder",
    "Startup Founders": "Startup Founder",
    "CFA": "Financial Expert",
    "CFO": "Senior Executive",
    "CFO": "Senior Executive",
    "COO": "Senior Executive",
    "CTO": "Startup Founder",
    "Company Secretary": "Financial Expert",
    "Consultant": "Business Advisor",
    "Designers": "Designer",
    "Director": "Senior Executive",
    "Engineers": "Engineer",
    "Entrepreneur": "SME Owner",
    "Finance Specialist": "Financial Expert",
    "Financial Advisor": "Financial Expert",
    "Financial Analyst": "Financial Expert",
    "Financial Experts": "Financial Expert",
    "Graphic Designer": "Designer",
    "Growth Hacker": "Marketing Expert",
    "Influencer": "Marketing Expert",
    "Investment fund": "Startup Investor",
    "Startup Investors": "Startup Investor",
    "Investor": "Startup Investor",
    "Journalist": "Marketing Expert",
    "Lawyers": "Lawyer",
    "Manager": "Business Development Executive",
    "Marketing Agency": "Marketing Expert",
    "Marketing Expert": "Marketing Expert",
    "Others": "Other",
    "Partner": "Senior Executive",
    "President": "Senior Executive",
    "Principal": "Senior Executive",
    "Product Managers": "Product Manager",
    "Professional": "Other",
    "Startup": "Startup Founder",
    "Students or Intern": "Student or Intern",
    "Thought Leader": "Senior Executive",
    "UI/UX Designer": "Designer",
    "Vice President": "Senior Executive",
    "Videographer": "Designer",
    "Writer": "Marketing Expert",
}


def fix_all_tags(dry_run=True, users=None):
    """Fix tags."""
    all_users = users if users else models.User.objects.all()

    for user in all_users:
        if not user.has_profile:
            continue

        print("Correcting tag for user: {}".format(user.email))
        profile = user.profile
        new_tag_obj = profile.new_tags.first()

        if not new_tag_obj:
            primary_tag_obj = profile.tags.first()
            primary_tag = primary_tag_obj.name if primary_tag_obj else "Other"
            corrected_new_tag = TAGS_TO_CORRECTED_TAGS_MATCH.get(primary_tag, "Other")
            print("Corrected tag for user: {}".format(corrected_new_tag))
            corrected_new_tag_obj, _ = tag_models.Tag.objects.get_or_create(name=corrected_new_tag)

            if not dry_run:
                profile.new_tag.add(corrected_new_tag_obj)
                print("Added new tag: {}".format(corrected_new_tag))
            continue

        new_tag = new_tag_obj.name if new_tag_obj else "Other"
        corrected_new_tag = TAGS_TO_CORRECTED_TAGS_MATCH.get(new_tag, "Other")
        print("Corrected tag for user: {}".format(corrected_new_tag))
        corrected_new_tag_obj, _ = tag_models.Tag.objects.get_or_create(name=corrected_new_tag)

        if not dry_run:
            profile.new_tag.clear()
            print("Removed old new tag.")
            profile.new_tag.add(corrected_new_tag_obj)
            print("Added new tag: {}".format(corrected_new_tag))
