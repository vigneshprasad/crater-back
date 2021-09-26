from integrations.dyte.service import dyte_service


def run(dry_run=True):

    all_webhooks_data = dyte_service.get_all_webhooks()

    print("Deleting webhooks with ids:")
    print([webhook["id"] for webhook in all_webhooks_data], "\n")

    for webhook in all_webhooks_data:
        print("Deleting Webhook: {}".format(webhook["id"]))

        if not dry_run:
            deleted = dyte_service.delete_webhook(
                webhook["id"]
            )
            if deleted:
                print("Deleted Webhook: {}".format(webhook["id"]))

        print("-----")
