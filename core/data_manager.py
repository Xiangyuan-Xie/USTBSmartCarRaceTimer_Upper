class DataManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.race_data = {
            "比赛进度": 0,
            "队伍名单": [
                {
                    "队伍编号": "Test",
                    "队伍名称": "Test",
                    "队伍成员": "Test",
                    "比赛阶段": "赛前准备阶段",
                    "剩余时间": self.config_manager.get("赛前准备时间", 90),
                    "是否暂停": True,
                    "所有成绩": [
                        {
                            "原始时间": 20.744,
                            "修正时间": 20.744,
                            "状态": "未处理",
                            "罚时": [],
                        },
                        {
                            "原始时间": 24.552,
                            "修正时间": 24.552,
                            "状态": "未处理",
                            "罚时": [],
                        },
                    ],
                    "最好成绩": 999.999,
                }
            ],
        }

    def get_current_team_index(self):
        return self.race_data["比赛进度"]

    def set_current_team_index(self, index):
        if 0 <= index < len(self.race_data["队伍名单"]):
            self.race_data["比赛进度"] = index

    def get_current_team(self):
        index = self.get_current_team_index()
        if 0 <= index < len(self.race_data["队伍名单"]):
            return self.race_data["队伍名单"][index]
        return None

    def get_team_list(self):
        return self.race_data["队伍名单"]

    def set_team_list(self, team_list):
        self.race_data["队伍名单"] = team_list
        # 重置比赛进度
        self.race_data["比赛进度"] = 0

    def next_team(self):
        if self.race_data["比赛进度"] < len(self.race_data["队伍名单"]) - 1:
            self.race_data["比赛进度"] += 1
            return True
        return False

    def previous_team(self):
        if self.race_data["比赛进度"] > 0:
            self.race_data["比赛进度"] -= 1
            return True
        return False
