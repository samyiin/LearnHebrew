"""
This file includes recite planners that can plan what thing to recite today.
There are some things to consider:
1. What happens if I missed yesterdays recite?
2. What if I want to customize my recite
3. What if user switched time zone?
"""
import datetime
from abc import ABC, abstractmethod


# class RecitePlanner(ABC):
#     """
#     This class represent a planner that will decide what should one recite today
#     """
#
#     @abstractmethod
#     def get_recite_datetime(self):
#         """
#
#         :return a list of date to recite (type: date)
#         """
#         pass
#
#     @abstractmethod
#     def get_recite_material(self):
#         """
#
#         :return: a list of objects that represents recite material
#         """
#         pass
#

class EbbinghausPlanner:
    """
    This class represent a planner that will decide what should one recite today
    This will only be initialized once for each user. Should I prepare for multi-user? #todo
    So far keep the precision of minutes in case there is a usage in the future.
    Now we set up a database, with columns:
    [reciteMaterial:BLOB, first_time: date, 1 day recite: Bool, 2 day recite, ......]

    Q&A:
    Q: What if I missed yesterdays recite?
    A: No scientific evidence for that for now: So simple ignore it and continue. If you missed day1, day 2, and today
    is day 4, you just do the day 4's recite for the material. Maybe later we can assess each material's recite history,
    to conjure if this material has been recited well.
    Q: What if I want to customize my recite?
    A: Write a get_xxx_recite_dates() function, and change get_recite_datetime()
    Q: What if user switched time zone?
    A: So far not considered, later simple change datetime to greenwich.
    """
    def get_recite_material(self):
        pass

    def get_recite_datetime(self):
        return self._get_normal_recite_dates()


    def _get_normal_recite_dates(self):
        """
        Normally, according to Ebbinghaus, dates to recite are:
        [yesterday, 2 days ago, 4 days ago, 7 days ago, 15 days ago, 1 month, 3 month, 6 month]
        If you want to be more specific, then also:
        [5 minutes, 30 minutes, 2 hours, 12 hours ago]
        This feature can be add later. #todo
        """
        recite_dates = []
        for i in [1, 2, 4, 7, 15, 30, 90, 180]:
            should_recite = datetime.datetime.now() - datetime.timedelta(days = i)
            recite_dates.append(should_recite.strftime("%Y-%m-%d"))
        return recite_dates




