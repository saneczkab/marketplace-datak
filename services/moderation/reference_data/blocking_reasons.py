from enum import Enum
from typing import TypedDict


class BlockingReasonCode(str, Enum):
	DESCRIPTION_MISMATCH = "DESCRIPTION_MISMATCH"
	COUNTERFEIT = "COUNTERFEIT"
	FORBIDDEN_GOODS = "FORBIDDEN_GOODS"


class BlockingReasonSeed(TypedDict):
	code: str
	title: str
	description: str | None
	hard_block: bool
	is_active: bool


BLOCKING_REASONS: list[BlockingReasonSeed] = [
	{
		"code": BlockingReasonCode.DESCRIPTION_MISMATCH.value,
		"title": "Описание не соответствует товару",
		"description": None,
		"hard_block": False,
		"is_active": True,
	},
	{
		"code": BlockingReasonCode.COUNTERFEIT.value,
		"title": "Контрафактный товар",
		"description": None,
		"hard_block": True,
		"is_active": True,
	},
	{
		"code": BlockingReasonCode.FORBIDDEN_GOODS.value,
		"title": "Товар запрещён к продаже на территории РФ",
		"description": None,
		"hard_block": True,
		"is_active": True,
	},
]
