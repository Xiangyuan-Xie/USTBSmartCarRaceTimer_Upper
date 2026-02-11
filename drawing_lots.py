#!/usr/bin/env python3
import random
import sys
from pathlib import Path

import pandas as pd
from loguru import logger

# Configure loguru for standalone script
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> - <level>{message}</level>",
)


def generate_order(group, seed):
    """Generate drawing order tags based on group and random seed"""
    group_dict = {"镜头组": 18, "电磁组": 20, "缩微光电组": 9}

    if group not in group_dict:
        raise ValueError(f"未知的组别: {group}")

    prefix = "A" if group == "镜头组" else "B" if group == "电磁组" else "D"
    order = [f"{prefix}{i}" for i in range(1, group_dict[group] + 1)]

    # Prevent seed overflow
    random.seed(seed % (2**32))
    random.shuffle(order)
    return order


def process_table(group, seed):
    file_prefix = "A" if group == "镜头组" else "B" if group == "电磁组" else "D"
    desktop_path = Path.home() / "Desktop"

    file_path = None
    for ext in [".xlsx", ".xls", ".csv"]:
        potential_file = desktop_path / f"{file_prefix}{ext}"
        if potential_file.exists():
            file_path = potential_file
            break

    if file_path is None:
        raise FileNotFoundError(
            f"未找到 {file_prefix} 表格文件，请放在桌面并命名为 {file_prefix}.xlsx 或 {file_prefix}.csv"
        )

    if file_path.suffix == ".csv":
        df = pd.read_csv(file_path, header=None)
    else:
        df = pd.read_excel(file_path, header=None)

    shuffled_order = generate_order(group, seed)
    if len(df) != len(shuffled_order):
        raise ValueError(f"表格行数({len(df)})与组别预期数({len(shuffled_order)})不一致")

    # Shuffle order
    df = df.sample(frac=1, random_state=seed % (2**32)).reset_index(drop=True)

    output_file = desktop_path / f"抽签结果_{group}.xlsx"

    # Save result (no index, no header)
    df.to_excel(output_file, index=False, header=False)

    return df, output_file


# Example run
if __name__ == "__main__":
    seed = 202511301213
    group = "电磁组"

    try:
        result_df, output_path = process_table(group, seed)
        logger.info(f"抽签结果已生成: {output_path}")
    except Exception as e:
        logger.error(f"错误: {e}")
