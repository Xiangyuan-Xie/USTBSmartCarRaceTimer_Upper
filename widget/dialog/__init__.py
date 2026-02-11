from .add_record import AddRecordDialog
from .base import BaseDialog, InfoDialog
from .communication_settings import CommunicationSettingDialog
from .competition_settings import CompetitionSettingDialog
from .modify_time import ModifyTimeDialog
from .penalty_setting import PenaltySettingDialog
from .timer_setting import TimerSettingDialog
from .screen_settings import ScreenSettingDialog

__all__ = [
    "InfoDialog",
    "BaseDialog",
    "AddRecordDialog",
    "ModifyTimeDialog",
    "CommunicationSettingDialog",
    "PenaltySettingDialog",
    "CompetitionSettingDialog",
    "TimerSettingDialog",
    "ScreenSettingDialog",
]
