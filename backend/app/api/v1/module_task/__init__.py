from fastapi import APIRouter

from .cronjob.job.controller import JobRouter
from .cronjob.node.controller import NodeRouter

task_router = APIRouter(prefix="/task")

task_router.include_router(JobRouter)
task_router.include_router(NodeRouter)
