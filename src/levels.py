from src.settings import GRID_SIZE, TileType


def get_empty_matrix():
    """Создание пустой матрицы игрового поля"""
    return [[0] * GRID_SIZE for _ in range(GRID_SIZE)]


def add_base(matrix):
    """Генерация базы и кирпичей вокруг"""
    for col in range(11, 15):
        matrix[23][col] = TileType.BRICK
    matrix[24][11] = TileType.BRICK
    matrix[24][14] = TileType.BRICK
    matrix[24][12] = TileType.BASE
    matrix[24][13] = TileType.BASE


def add_border(matrix):
    """Создание невидимой рамки по краю карты"""
    last = GRID_SIZE - 1
    for i in range(GRID_SIZE):
        matrix[0][i] = TileType.BORDER
        matrix[last][i] = TileType.BORDER
        matrix[i][0] = TileType.BORDER
        matrix[i][last] = TileType.BORDER


def finish_level(matrix):
    """Сборка компонентов уровня"""
    add_base(matrix)
    add_border(matrix)


lvl1 = get_empty_matrix()
for i in range(2, 22, 4):
    for j in range(2, 24):
        if j % 5 != 0:
            lvl1[j][i] = TileType.BRICK
finish_level(lvl1)

lvl2 = get_empty_matrix()
for i in range(1, 25):
    lvl2[11][i] = TileType.WATER
    lvl2[12][i] = TileType.WATER

for x in [5, 6, 19, 20]:
    lvl2[11][x] = 0
    lvl2[12][x] = 0

for i in [4, 9, 16, 21]:
    for j in range(2, 23):
        if j not in [10, 11, 12, 13]:
            lvl2[j][i] = TileType.CONCRETE if j % 4 == 0 else TileType.BRICK
finish_level(lvl2)

lvl3 = get_empty_matrix()
for j in range(6, 20):
    for i in range(5, 21):
        lvl3[j][i] = TileType.ICE

for j in range(2, 24):
    lvl3[j][2] = TileType.BUSH
    lvl3[j][3] = TileType.BUSH
    lvl3[j][22] = TileType.BUSH
    lvl3[j][23] = TileType.BUSH
finish_level(lvl3)

lvl4 = get_empty_matrix()
for i in range(2, 24):
    if i not in [5, 6, 7, 18, 19, 20]:
        lvl4[4][i] = TileType.CONCRETE

for j in [8, 9, 10, 15, 16, 17]:
    for i in [4, 5, 6, 19, 20, 21]:
        lvl4[j][i] = TileType.BRICK

for i in range(9, 17):
    lvl4[7][i] = TileType.BUSH
    lvl4[8][i] = TileType.BUSH
    lvl4[13][i] = TileType.BUSH
    lvl4[14][i] = TileType.BUSH
finish_level(lvl4)

lvl5 = get_empty_matrix()
for j in range(9, 17):
    for i in range(5, 21):
        lvl5[j][i] = TileType.MUD

for i in range(4, 22, 3):
    lvl5[7][i] = TileType.MINE
    lvl5[18][i] = TileType.MINE

for j in (11, 12, 13, 14):
    lvl5[j][2] = TileType.CONCRETE
    lvl5[j][23] = TileType.CONCRETE
for i in range(8, 18, 3):
    lvl5[4][i] = TileType.BRICK
    lvl5[5][i] = TileType.BRICK
finish_level(lvl5)

LEVELS = [lvl1, lvl2, lvl3, lvl4, lvl5]
