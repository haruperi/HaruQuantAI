from app.contracts.interfaces.operate_jobs import OperateJobsOperation, OperateJobsRequest
from app.contracts.orchestration.jobs import ControlIntent, DomainOutcome, JobAttempt, JobSemanticRecord
from app.services.interfaces.operate_jobs.gateway import JobsGateway


class Jobs:
    async def get_semantics(self, job_id):
        return JobSemanticRecord(job_id, JobAttempt("a", job_id, 1, 1, None), DomainOutcome.REFUSED, ControlIntent.NONE, ControlIntent.NONE, False, True, "fp", "input", "demo", None, job_id, 0, False)
    async def request_control(self, job_id, *, expected_version, control):
        record = await self.get_semantics(job_id)
        return JobSemanticRecord(record.job_id, record.current_attempt, record.domain_outcome, control, ControlIntent.NONE, False, True, record.request_fingerprint, record.input_ref, record.owner_operation, None, record.root_job_id, 0, False)


class Resources:
    def get_snapshot(self):
        return "snapshot"


class Workers:
    pass


async def test_preserves_domain_outcome_and_control_intent():
    gateway = JobsGateway(Jobs(), Resources(), Workers())
    record = await gateway.operate_jobs(OperateJobsRequest(OperateJobsOperation.GET_JOB, job_id="j"))
    assert record.domain_outcome is DomainOutcome.REFUSED
    controlled = await gateway.operate_jobs(OperateJobsRequest(OperateJobsOperation.REQUEST_CONTROL, job_id="j", expected_version=1, control=ControlIntent.CANCEL))
    assert controlled.desired_control is ControlIntent.CANCEL
    assert controlled.acknowledged_control is ControlIntent.NONE
