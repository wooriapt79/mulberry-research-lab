from fastapi import FastAPI

from api.middleware import ErrorPolicyMiddleware, RequestContextMiddleware
from api.routers import demo_router, health_router

app = FastAPI(title="Mulberry Research Lab - Reliability Sandbox")

# context 먼저, policy 다음
app.add_middleware(RequestContextMiddleware)
app.add_middleware(ErrorPolicyMiddleware, policy_path="services/reliability/error_policy.yaml")

app.include_router(health_router)
app.include_router(demo_router)
