from locust import HttpUser, task, between

class LoginRegisterLoadTest(HttpUser):
    wait_time = between(1,5)

    @task
    def get_login(self):
        self.client.get("/login-form")
    
    @task
    def get_register(self):
        self.client.get("/register")

    @task
    def get_admin(self):
        self.client.get("/admin")