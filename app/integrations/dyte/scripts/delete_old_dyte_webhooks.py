from integrations.dyte.service import dyte_service


def run(dry_run=True):

    print("Getting all Webhooks")
    all_webhooks = dyte_service.get_all_webhooks()
    all_webhooks_data = all_webhooks["data"]["webhooks"]

    print("Deleting webhooks")
    print([webhook["id"] for webhook in all_webhooks])

    for webhook in all_webhooks:
        print("Deleting Webhook: {}".format(webhook["id"]))

        if not dry_run:
            dyte_service.delete_webhook(
                webhook["id"]
            )
            print("Deleted Webhook: {}".format(webhook["id"]))

        print("-----")
