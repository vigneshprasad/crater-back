from locust import between, HttpUser, task


class QuickstartUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def series(self):
        self.client.get("/v1/groups/public/conversations/series/")

    @task
    def webinar(self):
        self.client.get("/v1/groups/conversations/webinars/all")

    @task
    def creator(self):
        self.client.get("/v1/crater/creator/")

    @task
    def featured(self):
        self.client.get("/v1/groups/public/conversations/webinars/featured")
