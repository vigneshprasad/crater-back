from users import models
from tags import models as tag_models


TAGS_TO_NEW_TAGS_MATCH = {
    "Accountant": "Financial Expert",
    "Associate": "Other",
    "Board Member": "Senior Executive",
    "Brand Advisor": "Marketing Expert",
    "Business Owner (SME)": "SME Owner",
    "Business Specialist": "Business Advisor",
    "CEO": "Startup Founder",
    "CFA": "Financial Expert",
    "CFO": "Senior Executive",
    "COO": "Senior Executive",
    "CTO": "Startup Founder",
    "Company Secretary": "Financial Expert",
    "Consultant": "Business Advisor",
    "Director": "Senior Executive",
    "Entrepreneur": "SME Owner",
    "Finance Specialist": "Financial Expert",
    "Financial Advisor": "Financial Expert",
    "Financial Analyst": "Financial Expert",
    "Graphic Designer": "Designer",
    "Growth Hacker": "Marketing Expert",
    "Influencer": "Marketing Expert",
    "Investment fund": "Startup Investor",
    "Investor": "Startup Investor",
    "Journalist": "Marketing Expert",
    "Manager": "Business Development Executive",
    "Marketing Agency": "Marketing Expert",
    "Partner": "Senior Executive",
    "President": "Senior Executive",
    "Principal": "Senior Executive",
    "Professional": "Other",
    "Startup": "Startup Founder",
    "Students or Intern": "Student/Intern",
    "Student or Intern": "Student/Intern",
    "Thought Leader": "Senior Executive",
    "UI/UX Designer": "Designer",
    "Vice President": "Senior Executive",
    "Videographer": "Designer",
    "Writer": "Marketing Expert",
    # New Changes.
    "Financial Experts": "Financial Expert",
    "Others": "Other",
    "HR Executives": "HR Executive",
    "Senior Executives": "Senior Executive",
    "Marketing Experts": "Marketing Expert",
    "Business Advisors": "Business Advisor",
    "Business Development Executives": "Business Development Executive",
    "SME Owners": "SME Owner",
    "Startup Founders": "Startup Founder",
    "Designers": "Designer",
    "Engineers": "Engineer",
    "Startup Investors": "Startup Investor",
    "Lawyers": "Lawyer",
    "Product Managers": "Product Manager",
}


def run(dry_run=True, users=None):
    """Migrate users with old tags and create a single new tag."""

    all_users = users if users else models.User.objects.all()

    for user in all_users:
        if not user.has_profile:
            continue
        print("Start", "*"*30)
        print("Updating tag for User: {}".format(user.email))
        profile = user.profile
        new_tag_obj = profile.new_tag.all().first()

        # If the user has not new tag, create on from old tags.
        if not new_tag_obj:
            old_tags_obj = profile.tags.first()
            old_tag = old_tags_obj.name if old_tags_obj else "Other"
            # Get new tag from the tag to new tag map.
            print("Old Tag: {}".format(old_tag))
            new_tag = TAGS_TO_NEW_TAGS_MATCH.get(old_tag, "Other")
            print("New Tag: {}".format(new_tag))

            if not dry_run:
                tag_obj, _ = tag_models.Tag.objects.get_or_create(name=new_tag)
                # Add the new tag and continue to the next user.
                profile.new_tag.add(tag_obj)
                print("Added new tag: {}".format(new_tag))

            print("End", "*" * 30)
            continue

        # If the user has new tag, migrate it to the correct new tag.
        new_tag = new_tag_obj.name
        print("Old Tag: {}".format(new_tag))
        correct_new_tag = TAGS_TO_NEW_TAGS_MATCH.get(new_tag, "Other")
        print("New Tag: {}".format(correct_new_tag))

        if not dry_run:
            tag_obj, _ = tag_models.Tag.objects.get_or_create(name=correct_new_tag)
            # Remove the old new tag, and add the corrected new tag.
            profile.new_tag.clear()
            print("Removed old new tag.")
            profile.new_tag.add(tag_obj)
            print("Added new tag: {}".format(correct_new_tag))

        print("End", "*" * 30)
