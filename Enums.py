import enum


class LastEntriesIDs():
    WallaNews = 0
    WallaSports = 0
    WallaFinance = 0
    WallaCars = 0
    WallaCelebs = 0
    WallaFashion = 0
    WallaFood = 0
    WallaTech = 0
    WallaTravel = 0


class URLs(enum.StrEnum):
    WallaNews = f'https://rss.walla.co.il/feed/1?type=main'
    WallaSports = f'https://rss.walla.co.il/feed/3?type=main'
    WallaFinance = f'https://rss.walla.co.il/feed/2?type=main'
    WallaCars = f'https://rss.walla.co.il/feed/31?type=main'
    WallaFashion = f'https://rss.walla.co.il/feed/24?type=main'
    WallaFood = f'https://rss.walla.co.il/feed/9?type=main'
    WallaTech = f'https://rss.walla.co.il/feed/6?type=main'
    WallaTravel = f'https://rss.walla.co.il/feed/14?type=main'


class WallaGroupsChatsIDs(enum.IntEnum):
    WallaNews = -1002337686071
    WallaSports = -1002280262853
    WallaFinance = -1002280850710
    WallaCars = -1002442038989
    WallaFashion = -1002336181784
    WallaFood = -1002454207048
    WallaTech = -1002270972271
    WallaTravel = -1002410002742
