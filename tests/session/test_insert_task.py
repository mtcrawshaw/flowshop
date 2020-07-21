"""
Unit test cases for insert_task() in flowshop/session.py.
"""

from datetime import datetime
from typing import List, Any

from flowshop.session import Session
from flowshop.task import Task


def list_exclude(l: List[Any], index: int) -> List[Any]:
    """ Helper function to exclude a single element from a list. """
    return l[:index] + l[index + 1 :]


def test_insert_task_empty_actual():
    """
    Insert a task into the actual schedule of an empty session.
    """

    # Construct session.
    session = Session("test")

    # Insert task.
    task = Task(
        "test",
        priority=1.0,
        start_time=datetime(2020, 5, 1, hour=12),
        end_time=datetime(2020, 5, 1, hour=13, minute=30),
    )
    session.insert_task(
        planned=False, task=task,
    )

    # Test session values.
    assert session.history_pos == 1
    assert len(session.edit_history) == 2
    assert len(session.edit_history[0][0].tasks) == 0
    assert len(session.edit_history[0][1].tasks) == 0
    assert len(session.edit_history[1][0].tasks) == 0
    assert len(session.edit_history[1][1].tasks) == 1
    assert session.edit_history[1][1].tasks[0] == task


def test_insert_task_empty_planned():
    """
    Insert a task into the planned schedule of an empty session.
    """

    # Construct session.
    session = Session("test")

    # Insert task.
    task = Task(
        "test",
        priority=1.0,
        start_time=datetime(2020, 5, 1, hour=12),
        end_time=datetime(2020, 5, 1, hour=13, minute=30),
    )
    session.insert_task(
        planned=True, task=task,
    )

    # Test session values.
    assert session.history_pos == 1
    assert len(session.edit_history) == 2
    assert len(session.edit_history[0][0].tasks) == 0
    assert len(session.edit_history[0][1].tasks) == 0
    assert len(session.edit_history[1][0].tasks) == 1
    assert len(session.edit_history[1][1].tasks) == 0
    assert session.edit_history[1][0].tasks[0] == task


def test_insert_task_nonempty_actual():
    """
    Insert a task into the planned schedule of an empty session.
    """

    # Construct session.
    session = Session("example", load=True)

    # Store pre-insert session values.
    pre_history_pos = session.history_pos
    pre_edit_history = list(session.edit_history)

    # Insert task.
    task = Task(
        "test",
        priority=1.0,
        start_time=datetime(2020, 5, 1, hour=15),
        end_time=datetime(2020, 5, 1, hour=16),
    )
    session.insert_task(
        planned=False, task=task,
    )

    # Test session values.
    assert session.history_pos == pre_history_pos + 1
    assert len(session.edit_history) == len(pre_edit_history) + 1
    assert session.edit_history[:-1] == pre_edit_history
    assert session.edit_history[-1][0] == pre_edit_history[-1][0]
    assert (
        list_exclude(session.edit_history[-1][1].tasks, 2)
        == pre_edit_history[-1][1].tasks
    )
    assert session.edit_history[-1][1].tasks[2] == task


def test_others():
    """
    We should also add some cases to check that tasks get sorted correctly, and where an
    overlapping task is given.
    """

    raise NotImplementedError