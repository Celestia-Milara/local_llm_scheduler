import logging

# 设置日志
logger = logging.getLogger(__name__)

# 校内常见地标之间的预设步行时间（分钟）
# 使用 frozenset 作为键，以确保 (A, B) 和 (B, A) 映射到相同的值
CAMPUS_DISTANCES = {
    frozenset(["图书馆", "实验楼"]): 15,
    frozenset(["图书馆", "食堂"]): 10,
    frozenset(["实验楼", "食堂"]): 12,
    frozenset(["图书馆", "行政楼"]): 8,
    frozenset(["行政楼", "校门"]): 5,
    frozenset(["宿舍", "食堂"]): 5,
    frozenset(["宿舍", "图书馆"]): 20,
    frozenset(["宿舍", "实验楼"]): 25,
}

def get_travel_time(origin: str, destination: str) -> int:
    """
    计算两地之间的预计通勤时间（分钟）。

    Args:
        origin (str): 起点名称
        destination (str): 终点名称

    Returns:
        int: 预计步行分钟数
    """
    if not origin or not destination or origin == destination:
        return 0

    origin = origin.strip()
    destination = destination.strip()

    route_key = frozenset([origin, destination])

    travel_time = CAMPUS_DISTANCES.get(route_key)

    if travel_time is not None:
        logger.debug(f"Found preset travel time for {origin} -> {destination}: {travel_time} min")
        return travel_time

    # 兜底默认值
    default_time = 10
    logger.info(f"No preset distance for {origin} -> {destination}. Using default: {default_time} min")

    return default_time
