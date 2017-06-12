# coding=utf-8
import typing

from src.utils.custom_session import JSONObject, json_property


class AVJob(JSONObject):

    @json_property
    def jobId(self):
        """"""

    @json_property
    def name(self):
        """"""

    @json_property
    def allowFailure(self):
        """"""

    @json_property
    def messagesCount(self):
        """"""

    @json_property
    def compilationMessagesCount(self):
        """"""

    @json_property
    def compilationErrorsCount(self):
        """"""

    @json_property
    def compilationWarningsCount(self):
        """"""

    @json_property
    def testsCount(self):
        """"""

    @json_property
    def passedTestsCount(self):
        """"""

    @json_property
    def failedTestsCount(self):
        """"""

    @json_property
    def artifactsCount(self):
        """"""

    @json_property
    def status(self):
        """"""

    @json_property
    def started(self):
        """"""

    @json_property
    def finished(self):
        """"""

    @json_property
    def created(self):
        """"""

    @json_property
    def updated(self):
        """"""


class AVAllJobs(JSONObject):
    def __iter__(self):
        for x in self.json:
            yield AVJob(x)

    def successful_only(self) -> typing.Generator[AVJob, None, None]:
        for x in self:
            if x.status == 'success':
                yield x

    def with_artifacts(self) -> typing.Generator[AVJob, None, None]:
        for x in self:
            if int(x.artifactsCount) > 0:
                yield x

    def __getitem__(self, job_id) -> AVJob:
        if isinstance(job_id, int):
            if job_id > self.__len__() - 1:
                raise IndexError(job_id)
            else:
                return AVJob(self.json[job_id])
        elif isinstance(job_id, str):
            for job in self:
                if job.jobId == job_id:
                    return job
            raise AttributeError('no job found with name: {}'.format(job_id))

        raise NotImplementedError('__getitem__ not implemented for type: {}'.format(type(job_id)))

    def __len__(self) -> int:
        return len(self.json)

    def __contains__(self, job_id) -> bool:
        try:
            self.__getitem__(job_id)
            return True
        except AttributeError:
            return False
