from common.frozenmodel import Label
from datetime import datetime
from typing import List

class Cell:
    column: str
    row: int

    def __init__(self, inputCell: str):
        self.column = inputCell[0]
        self.row = int(inputCell[1:])
    
    def __str__(self) -> str:
        return f'{self.column}{self.row}'
    
    def minusRows(self, rows: int, *, min_row: int = 1) -> 'Cell':
        return Cell(f'{self.column}{max(min_row, self.row - rows)}')


class RangeData:
    sheetName: str
    startCell: Cell
    endCell: Cell

    def __init__(self, inputRange: str):
        self.sheetName, _, inputCells = inputRange.partition('!')
        cells = inputCells.split(':')
        self.startCell = Cell(cells[0])
        self.endCell = Cell(cells[0 if len(cells) == 1 else 1])

    def __str__(self) -> str:
        return f'{self.sheetName}!{str(self.startCell)}:{str(self.endCell)}'

    @classmethod
    def of(cls, *, sheetName: str, start: Cell, end: Cell) -> 'RangeData':
        return RangeData(f'{sheetName}!{str(start)}:{str(end)}')


class ClassificationRow:
    date: datetime
    classification: Label
    was_posted: bool

    def __init__(self, *, date: datetime, classification: Label, was_posted: bool):
        self.date = date
        self.classification = classification
        self.was_posted = was_posted
    
    def asList(self) -> List[str]:
        return [
            self.datetime.strftime('%Y-%m-%dT%H:%M:%S%z'),
            self.classification.value,
            'TRUE' if self.was_posted else 'FALSE',
        ]
