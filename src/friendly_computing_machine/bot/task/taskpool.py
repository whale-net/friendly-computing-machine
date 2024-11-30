import time
from datetime import timedelta

from friendly_computing_machine.db.dal import insert_task_instances
from friendly_computing_machine.bot.task.abstracttask import AbstractTask
from friendly_computing_machine.bot.task.findteams import FindTeams
from friendly_computing_machine.bot.task.findusers import FindUsers
from friendly_computing_machine.models.task import TaskInstanceStatus


class TaskPool:
    def __init__(
        self, sleep_period=timedelta(seconds=5), log_skipped_tasks: bool = False
    ):
        self._tasks: set[AbstractTask] = set()
        self._sleep_period_seconds = sleep_period.total_seconds()
        self.__should_run = True
        self._is_finalized: bool = False
        self._log_skipped_tasks = log_skipped_tasks

    def add_task(self, task: AbstractTask):
        if self._is_finalized:
            raise RuntimeError("task pool already finalized")
        self._tasks.add(task)

    def finalize(self):
        # get task config for the pool
        # for now, just everything
        self._is_finalized = True

    def start(self):
        if not self._is_finalized:
            self.finalize()
        while self.__should_run:
            self._process_tasks()
            time.sleep(self._sleep_period_seconds)

    def _process_tasks(self):
        # TODO - thread pool this
        # most tasks will be API calls
        instances = []
        for task in self._tasks:
            instances.append(task.run())

        if not self._log_skipped_tasks:
            instances = [
                instance
                for instance in instances
                if instance.status != TaskInstanceStatus.SKIPPED
            ]

        insert_task_instances(instances)

    def stop(self):
        """
        stop taskpool, intended to be externally triggered

        :return:
        """
        self.__should_run = False


def create_default_taskpool() -> TaskPool:
    # unsure how to specify which tasks I actually want, so just going to make this register everything for now
    # with the option to comment out individual ones while I work on this
    tp = TaskPool()
    tp.add_task(FindTeams())
    tp.add_task(FindUsers())
    return tp
