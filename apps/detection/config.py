# coding:utf-8
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 图片及视频检测结果保存路径（相对于 media 目录）
save_path = BASE_DIR / 'media' / 'results'

# 使用的模型路径
model_path = BASE_DIR / 'models' / 'best.pt'

# 字体路径
font_path = BASE_DIR / 'Font' / 'platech.ttf'

# 类别名称映射
names = {
    0: 'lighter',
    1: 'pressure',
    2: 'knife',
    3: 'scissors',
    4: 'powerbank',
    5: 'zippooil',
    6: 'handcuffs',
    7: 'slingshot',
    8: 'firecrackers',
    9: 'nailpolish'
}

# 中文名称映射
CH_names = [
    '打火机',
    '压力罐',
    '刀具',
    '剪刀',
    '充电宝',
    'ZIPPO油',
    '手铐',
    '弹弓',
    '鞭炮',
    '指甲油'
]



