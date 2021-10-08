from typing import Union

from elements import EleTy, ELE_TY_sel_idx_rng, EleVal


class IdxRngSel:

    @classmethod
    def ele_ty(cls) -> EleTy:
        return ELE_TY_sel_idx_rng

    @classmethod
    def from_ele_val(cls, ele_val: EleVal) -> EleVal:
        ele_val.val_mp = cls(ele_val.val)
        return ele_val

    def __init__(self, idx_rng_str: str, f_asort=True) -> None:
        super().__init__()
        if idx_rng_str:
            self.idx_li: list[int] = [int(i) for i in idx_rng_str.split(',')]
        else:
            self.idx_li = []

        self.f_asort = f_asort
        if self.f_asort:
            self.idx_li.sort()

    def toggle(self, idx: Union[int, str]):
        v = int(idx)
        if v in self.idx_li:
            self.idx_li.remove(v)
        else:
            self.idx_li.append(v)
        if self.f_asort:
            self.idx_li.sort()

    def to_idx_rng_str(self) -> str:
        return ','.join([str(i) for i in self.idx_li])

    def is_empty(self) -> bool:
        return len(self.idx_li) == 0
