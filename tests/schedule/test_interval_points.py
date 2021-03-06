"""
Unit test cases for flowshop/task.py.
"""

from datetime import datetime

from flowshop import Schedule, Task


def test_interval_points_small():
    """
    Test Schedule.interval_points() for a small example.
    """

    task1 = Task(
        "task1",
        priority=1.5,
        start_time=datetime(2020, 5, 1, hour=12),
        end_time=datetime(2020, 5, 1, hour=13, minute=30),
    )
    task2 = Task(
        "task2",
        priority=2.0,
        start_time=datetime(2020, 5, 1, hour=13, minute=30),
        end_time=datetime(2020, 5, 1, hour=14, minute=30),
    )
    task3 = Task(
        "task3",
        priority=2.0,
        start_time=datetime(2020, 5, 8, hour=13, minute=30),
        end_time=datetime(2020, 5, 8, hour=14, minute=30),
    )
    schedule = Schedule("test", [task1, task2, task3])

    start_time = datetime(2020, 5, 1)
    end_time = datetime(2020, 5, 8)
    assert schedule.interval_points(start_time, end_time) == 4.25


def test_interval_points_empty():
    """
    Test Schedule.points() for an empty example.
    """

    task1 = Task(
        "task1",
        priority=1.5,
        start_time=datetime(2020, 5, 1, hour=12),
        end_time=datetime(2020, 5, 1, hour=13, minute=30),
    )
    task2 = Task(
        "task2",
        priority=2.0,
        start_time=datetime(2020, 5, 1, hour=13, minute=30),
        end_time=datetime(2020, 5, 1, hour=14, minute=30),
    )
    task3 = Task(
        "task3",
        priority=2.0,
        start_time=datetime(2020, 5, 8, hour=13, minute=30),
        end_time=datetime(2020, 5, 8, hour=14, minute=30),
    )
    schedule = Schedule("test", [task1, task2, task3])

    start_time = datetime(2020, 4, 1)
    end_time = datetime(2020, 4, 8)
    assert schedule.interval_points(start_time, end_time) == 0.0
