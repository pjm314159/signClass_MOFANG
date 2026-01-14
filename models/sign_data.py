"""
签到相关数据模型定义
定义了签到和课程的数据结构
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class Sign:
    """签到数据类

    Attributes:
        sign_type: 签到类型 ('gps', 'password', 'qrcode', 'rollCall')
        status: 签到状态 (0: 已签, 1: 未签, -1: 特殊情况)
        deadline: 过期时间戳
        class_id: 课程ID
        start_time: 开始时间戳
        params: 位置签到参数 (仅限GPS签到类型)
        sign_url: 签到URL
        sign_id: 签到ID
        salt: Salt值，用于推算签到ID
    """
    sign_type: str  # 'gps', 'password', 'qrcode', 'rollCall'
    status: int  # 0: 已签, 1: 未签, -1: 特殊情况
    deadline: Optional[int]  # 过期时间戳
    class_id: str
    start_time: Optional[int] = 0
    # 类型特定字段
    params: Optional[Dict[str, Any]] = None  # 位置签到参数
    sign_url: Optional[str] = None
    sign_id: Optional[int] = None
    salt: Optional[int] = None # 发布一个签到，得到一个sign_id，可以通过这个值往前推几个得到sign_id
@dataclass
class Class:
    """课程数据类

    Attributes:
        class_id: 课程ID
        name: 课程名称
        signs: 课程中的签到列表
    """
    class_id: str
    name: str
    signs: List[Sign]
if __name__ == "__main__":
    Sign( sign_type="", status=-1, deadline=-1,class_id="sad")
    Sign.sign_id = 45