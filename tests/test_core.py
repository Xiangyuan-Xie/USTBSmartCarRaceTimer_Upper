import os
import tempfile
import unittest

from core.config_manager import ConfigManager
from core.data_manager import DataManager


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary config file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8")
        self.temp_file.close()
        self.config_manager = ConfigManager(self.temp_file.name)

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_default_config(self):
        """Test if default config is loaded when file is empty/invalid"""
        self.assertEqual(self.config_manager.get("比赛名称"), "北京科技大学智能汽车竞赛")
        self.assertEqual(self.config_manager.get("赛前准备时间"), 90)

    def test_save_and_load_config(self):
        """Test saving and reloading configuration"""
        self.config_manager.set("比赛名称", "Test Competition")
        self.config_manager.set("赛前准备时间", 120)
        self.config_manager.save_config()

        # Reload
        new_manager = ConfigManager(self.temp_file.name)
        self.assertEqual(new_manager.get("比赛名称"), "Test Competition")
        self.assertEqual(new_manager.get("赛前准备时间"), 120)

    def test_group_key_mapping(self):
        """Test automatic key update based on group"""
        self.config_manager.set("比赛组别", "摄像头组")
        self.config_manager._update_key_based_on_group()
        self.assertEqual(self.config_manager.get("Key"), "220dfce992d21aea4507065760ddfce7")


class TestDataManager(unittest.TestCase):
    def setUp(self):
        # Mock ConfigManager
        self.mock_config = ConfigManager("non_existent_config.json")
        self.data_manager = DataManager(self.mock_config)

    def test_initial_state(self):
        """Test initial state of DataManager"""
        self.assertEqual(self.data_manager.get_current_team_index(), 0)
        team = self.data_manager.get_current_team()
        self.assertIsNotNone(team)
        self.assertEqual(team["队伍编号"], "Test")

    def test_navigation(self):
        """Test next_team and previous_team navigation"""
        # Create dummy team list with 3 teams
        teams = [
            {"队伍编号": "1", "队伍名称": "Team A", "剩余时间": 100},
            {"队伍编号": "2", "队伍名称": "Team B", "剩余时间": 100},
            {"队伍编号": "3", "队伍名称": "Team C", "剩余时间": 100},
        ]
        self.data_manager.set_team_list(teams)

        self.assertEqual(self.data_manager.get_current_team_index(), 0)
        self.assertEqual(self.data_manager.get_current_team()["队伍编号"], "1")

        # Go next
        self.assertTrue(self.data_manager.next_team())
        self.assertEqual(self.data_manager.get_current_team_index(), 1)
        self.assertEqual(self.data_manager.get_current_team()["队伍编号"], "2")

        # Go next again
        self.assertTrue(self.data_manager.next_team())
        self.assertEqual(self.data_manager.get_current_team_index(), 2)

        # Go next (should fail)
        self.assertFalse(self.data_manager.next_team())
        self.assertEqual(self.data_manager.get_current_team_index(), 2)

        # Go back
        self.assertTrue(self.data_manager.previous_team())
        self.assertEqual(self.data_manager.get_current_team_index(), 1)


if __name__ == "__main__":
    unittest.main()
