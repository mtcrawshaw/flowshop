""" Session object for editing schedules. """

from datetime import datetime, date, time, timedelta
from copy import deepcopy
from typing import List, Tuple, Dict, Any

from flowshop.schedule import Schedule
from flowshop.task import Task
from flowshop.files import saved_session_exists, save_session, load_session_state_dict


HISTORY_LEN = 100


class Session:
    """ Session object for editing schedules. """

    def __init__(self, name: str, load=False) -> None:
        """ Init function for Session object. """

        self.name: str = name

        # self.edit_history represents the history of schedules through changes, so that
        # we can implement undo and redo. self.history_pos holds the position within
        # history of the current schedule. The 0th slot is for the planned schedule, the
        # 1st is for the actual schedule.
        self.edit_history: List[Tuple[Schedule, Schedule]] = []
        self.history_pos: int = -1

        # self.base_date is the date of the Monday of the week which is currently being
        # edited.
        self.base_date = None

        # State variables that are saved and loaded during pickling.
        self.state_vars: List[str] = [
            "name",
            "edit_history",
            "history_pos",
            "base_date",
        ]

        # Load a session in, if necessary.
        if load:
            self.load_from(name)

        else:

            # Check to make sure there exists no saved session with given name.
            if saved_session_exists(name):
                raise ValueError("Already a saved session with name %s." % name)

            # Initialize edit history with empty schedules, and set base date to the
            # Monday of the current week. The 0-th entry is the planned schedule, and
            # the 1-st entry is the actual schedule.
            self.edit_history.append(
                (Schedule("%s_planned" % self.name), Schedule("%s_actual" % self.name))
            )
            self.history_pos = 0
            self.base_date = date.today()
            self.base_date -= timedelta(days=self.base_date.weekday())

    def save(self) -> None:
        """ Save session to file. """
        save_session(self)

    def load_from(self, name: str) -> None:
        """ Load session info from saved session. """

        # Check to make sure saved session exists.
        if not saved_session_exists(name):
            raise ValueError("No saved session with name %s." % name)

        # Load in session.
        state_dict = load_session_state_dict(name)
        self.copy_from_state_dict(state_dict)

    def copy_from_state_dict(self, state_dict: Dict[str, Any]) -> None:
        """ Copy state from state dict. """

        for state_var in self.state_vars:
            setattr(self, state_var, state_dict[state_var])

    def state_dict(self) -> Dict[str, Any]:
        """ Return dictionary holding state variables. """

        return {state_var: getattr(self, state_var) for state_var in self.state_vars}

    def current_schedules(self) -> Tuple[Schedule, Schedule]:
        """ Return schedules at current point in edit history. """

        return self.edit_history[self.history_pos]

    def set_new_schedules(self, planned: Schedule, actual: Schedule) -> None:
        """
        Set a new pair of schedules at the current position in the edit history. If
        necessary, we overwrite the edit history. There are three cases. The first is
        that the history position is maximal (i.e. there is nothing to redo), in which
        case we append the new schedules to the history and increment the history
        position. The second is that the history position doesn't point to the end of
        history, and the new schedules aren't equal to the next point in history.  In
        this case we wipe the history which comes after the current point, append the
        new schedules to the history, and increment the history position. Finally, if
        the history position doesn't point to the end of history, but the new schedules
        are equal to the next point in history, we simply increment the history position
        (equivalent to a redo operation).
        """

        if self.history_pos == len(self.edit_history) - 1:

            # First case.
            self.edit_history.append((planned, actual))
            self.history_pos = len(self.edit_history) - 1

        else:
            if (planned, actual) != self.edit_history[self.history_pos + 1]:

                # Second case.
                self.edit_history = self.edit_history[: self.history_pos + 1]
                self.edit_history.append((planned, actual))
                self.history_pos += 1
            else:

                # Third case.
                self.history_pos += 1

    def move_week(self, forward: bool = True) -> None:
        """
        Move the displayed days forward or backward one week in time.
        """

        self.base_date += (1 if forward else -1) * timedelta(days=7)

    def get_task(self, planned: bool, day: int, task_index: int) -> None:
        """
        Return a task from planned/actual, given a day and a task index.
        """

        planned_schedule, actual_schedule = self.current_schedules()
        target = planned_schedule if planned else actual_schedule
        task_date = self.base_date + timedelta(days=day)
        overall_index = target.get_task_index(task_date, task_index)
        return target.tasks[overall_index]

    def edit_task(
        self, planned: bool, day: int, task_index: int, new_values: Dict[str, Any]
    ) -> None:
        """ Edit a task in the current session by providing new values. """

        # Create new schedule objects to represent edited schedules.
        current_schedules = self.current_schedules()
        new_planned = deepcopy(current_schedules[0])
        new_actual = deepcopy(current_schedules[1])

        # Set values in new schedule objects.
        target = new_planned if planned else new_actual
        task_date = self.base_date + timedelta(days=day)
        overall_index = target.get_task_index(task_date, task_index)
        for param, new_val in new_values.items():
            setattr(target.tasks[overall_index], param, new_val)
        target._sort_tasks()
        target.check_for_overlap()

        # Set new schedule objects as current schedules.
        self.set_new_schedules(new_planned, new_actual)

    def insert_task(
        self,
        day: int,
        planned: bool,
        name: str,
        priority: float,
        start_time: time,
        hours: float,
    ) -> None:
        """ Insert a task into the current session. """

        # Create new schedule objects to represent edited schedules.
        current_schedules = self.current_schedules()
        new_planned = deepcopy(current_schedules[0])
        new_actual = deepcopy(current_schedules[1])

        # Construct task.
        task_date = self.base_date + timedelta(days=day)
        start = datetime.combine(task_date, start_time)
        end = start + timedelta(hours=hours)
        task = Task(name, priority, start, end)

        # Set values in new schedule objects.
        target = new_planned if planned else new_actual
        target.add_task(task)

        # Set new schedule objects as current schedules.
        self.set_new_schedules(new_planned, new_actual)

    def delete_task(self, planned: bool, day: int, task_index: int) -> None:
        """ Delete a task in the current session. """

        # Create new schedule objects to represent edited schedules.
        current_schedules = self.current_schedules()
        new_planned = deepcopy(current_schedules[0])
        new_actual = deepcopy(current_schedules[1])

        # Set values in new schedule objects.
        target = new_planned if planned else new_actual
        task_date = self.base_date + timedelta(days=day)
        overall_index = target.get_task_index(task_date, task_index)
        target.remove_task(overall_index)

        # Set new schedule objects as current schedules.
        self.set_new_schedules(new_planned, new_actual)

    def move_tasks(
        self,
        planned: bool,
        day: int,
        start_task_index: int,
        end_task_index: int,
        time_delta: timedelta,
    ) -> None:
        """ Move a contiguous sequence of tasks in time. """

        # Create new schedule objects to represent edited schedules.
        current_schedules = self.current_schedules()
        new_planned = deepcopy(current_schedules[0])
        new_actual = deepcopy(current_schedules[1])

        # Set values in new schedule objects.
        target = new_planned if planned else new_actual
        task_date = self.base_date + timedelta(days=day)
        overall_start_index = target.get_task_index(task_date, start_task_index)
        overall_end_index = overall_start_index + (end_task_index - start_task_index)
        for task_index in range(overall_start_index, overall_end_index):
            target.tasks[task_index].start_time += time_delta
            target.tasks[task_index].end_time += time_delta
        target._sort_tasks()
        target.check_for_overlap()

        # Set new schedule objects as current schedules.
        self.set_new_schedules(new_planned, new_actual)

    def undo(self) -> None:
        """ Undo last change, i.e. move to previous schedule in edit history. """
        self.history_pos = max(self.history_pos - 1, 0)

    def redo(self) -> None:
        """ Redo last change, i.e. move to next schedule in edit history. """
        self.history_pos = min(self.history_pos + 1, len(self.edit_history) - 1)

    def daily_points(self, day: int, planned: bool, cumulative: bool) -> float:
        """
        Compute points for a given day in the current week, either for planned or actual
        schedule and potentially cumulative from the beginning of the week.
        """

        # Construct interval over which to compute points.
        current_date = self.base_date + timedelta(days=day)
        start = self.base_date if cumulative else current_date
        end = current_date + timedelta(days=1)
        start_time = datetime(start.year, start.month, start.day)
        end_time = datetime(end.year, end.month, end.day)

        # Compute points in interval.
        planned_schedule, actual_schedule = self.current_schedules()
        schedule = planned_schedule if planned else actual_schedule
        tasks = schedule.tasks_in_interval(start_time, end_time)
        points = sum(task.points() for task in tasks)

        return points

    def daily_score(self, day: int, cumulative: bool) -> float:
        """
        Compute score for a given day in the current week, either for the individual day
        or cumulative from the beginning of the week.
        """

        planned_points = self.daily_points(day, planned=True, cumulative=cumulative)
        actual_points = self.daily_points(day, planned=False, cumulative=cumulative)

        if planned_points == 0.0:
            score = 100.0
        else:
            score = 100.0 * actual_points / planned_points

        return score
