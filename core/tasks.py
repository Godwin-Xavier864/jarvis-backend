from celery import shared_task
from core.agent.groq_client import run_groq_agent


@shared_task(bind=True, soft_time_limit=20)
def agent_task(self, messages):
    return run_groq_agent(messages)
