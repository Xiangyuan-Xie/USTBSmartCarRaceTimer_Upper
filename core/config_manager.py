import json
import logging
import os


class ConfigManager:
    # 组别到Key的映射关系（统一管理，避免重复定义）
    GROUP_KEY_MAPPING = {
        "摄像头组": "220dfce992d21aea4507065760ddfce7",
        "电磁组": "46840a1abb9fa373fe8daa1991bd53cd",
        "缩微光电组": "141d48c6c30c722025d1e75e1fafcb87"
    }

    DEFAULT_CONFIG = {
        "比赛名称": "北京科技大学智能汽车竞赛",
        "比赛阶段": "第二次分站赛",
        "比赛组别": "摄像头组",
        "速度计算": False,
        "赛道长度": 0,
        "赛前准备时间": 90,
        "比赛时间": 600,
        "罚时种类": [("停车失败", -10), ("碰撞小型路障", -10)],
        "SSID": "LAPTOP-XXY",
        "Password": "12345000",
        "Key": "",
        "投屏缩放比例": 1.0  # 投屏分辨率缩放比例，默认1.0（100%）
    }

    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            logging.warning(f"配置文件 {self.config_path} 不存在，使用默认配置。")
            # 即使不存在配置文件，也要根据默认组别设置Key
            self._update_key_based_on_group()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                # 处理罚时种类格式
                if "罚时种类" in data and isinstance(data["罚时种类"], list):
                    data["罚时种类"] = [tuple(item) if isinstance(item, list) else item for item in data["罚时种类"]]

                self.config.update(data)

                # 检查缺失配置
                missing_keys = [key for key in self.DEFAULT_CONFIG if key not in data]
                if missing_keys:
                    logging.warning(f"配置文件缺失以下键: {missing_keys}，已使用默认值。")
            
            # 根据比赛组别自动配置Key
            self._update_key_based_on_group()

        except Exception as e:
            logging.error(f"读取配置文件失败: {e}，将使用默认配置。")
            self._update_key_based_on_group()

    def _update_key_based_on_group(self):
        """根据比赛组别自动配置Key"""
        group_name = self.config.get("比赛组别", "")
        if group_name in self.GROUP_KEY_MAPPING:
            old_key = self.config.get("Key", "未设置")
            new_key = self.GROUP_KEY_MAPPING[group_name]
            self.config["Key"] = new_key
            if old_key != new_key:
                logging.info(f"根据组别自动更新Key: 组别={group_name}, 旧Key={old_key}, 新Key={new_key}")
            else:
                logging.info(f"根据组别自动配置Key: 组别={group_name}, Key={new_key}")


    def save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as file:
                json.dump(self.config, file, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

    def __getitem__(self, item):
        return self.config[item]

    def __setitem__(self, key, value):
        self.config[key] = value
