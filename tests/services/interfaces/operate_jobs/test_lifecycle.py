import pytest
from app.contracts.interfaces.operate_jobs import OperateJobsOperation, OperateJobsRequest
from app.services.interfaces.operate_jobs.gateway import JobsGateway


class Jobs: pass
class Resources:
    def get_snapshot(self): return "snapshot"
class Workers: pass


async def test_close_withdraws_translation_without_touching_owners():
    gateway = JobsGateway(Jobs(), Resources(), Workers())
    gateway.close()
    with pytest.raises(RuntimeError):
        await gateway.operate_jobs(OperateJobsRequest(OperateJobsOperation.RESOURCE_SNAPSHOT))
