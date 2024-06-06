from datetime import datetime
from common.frozenmodel import Label
from typing import List, Optional


class ClassificationRow:
    date: datetime
    classification: Label
    was_posted: Optional[bool]

    def __init__(self, *, date: datetime, classification: Label, was_posted: Optional[bool] = None):
        self.date = date
        self.classification = classification
        self.was_posted = was_posted

    def as_list(self) -> List[str]:
        return [self.date.strftime('%Y-%m-%dT%H:%M:%S'), self.classification.value, 'TRUE' if self.was_posted else 'FALSE']

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(date={self.date.strftime("%Y-%m-%dT%H:%M:%S")} classification={self.classification.value} was_posted={self.was_posted})'


class Cell:
    column: str
    row: int

    def __init__(self, input_cell: str):
        self.column = input_cell[0]
        self.row = int(input_cell[1:])

    def __str__(self) -> str:
        return f'{self.column}{self.row}'

    def minus_rows(self, rows: int, *, min_row: int = 1) -> 'Cell':
        return Cell(f'{self.column}{max(min_row, self.row - rows)}')


class RangeData:
    sheet_name: str
    start_cell: Cell
    end_cell: Cell

    def __init__(self, input_range: str):
        self.sheet_name, _, input_cells = input_range.partition('!')
        cells = input_cells.split(':')
        self.start_cell = Cell(cells[0])
        self.end_cell = Cell(cells[0 if len(cells) == 1 else 1])

    def __str__(self) -> str:
        return f'{self.sheet_name}!{str(self.start_cell)}:{str(self.end_cell)}'

    @classmethod
    def of(cls, *, sheet_name: str, start: Cell, end: Cell) -> 'RangeData':
        return RangeData(f'{sheet_name}!{str(start)}:{str(end)}')
