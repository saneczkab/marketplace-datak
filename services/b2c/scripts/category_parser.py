import sys
from typing import AsyncGenerator, Generator
import asyncio
from pathlib import Path
import openpyxl
from deep_translator import GoogleTranslator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
	sys.path.insert(0, PROJECT_ROOT)


from core.db import get_db  # noqa: E402
from database.models.catalog.base import Category  # noqa: E402


async def clear_db(db_session: AsyncSession) -> True:
	await db_session.execute(delete(Category))
	await db_session.commit()
	return True


async def translator(name: str) -> str:

	translated = await asyncio.to_thread(
		GoogleTranslator(source="ru", target="en").translate, name.strip()
	)

	return translated.lower().replace(" ", "-").replace("_", "-")


async def add_root_category(db_session: AsyncGenerator) -> None:

	root_category: Category = Category(
		name="Все товары",
		slug="all",
		description="Все товары",
		parent_id=None,
		is_active=True,
	)
	db_session.add(root_category)
	await db_session.commit()
	await db_session.refresh(root_category)


async def add_category_in_db(path: list, db_session: AsyncSession) -> bool:

	parent_id = None
	for parent_name in path[0 : len(path) - 1]:
		result = await db_session.execute(
			select(Category).where(
				Category.name == parent_name, Category.parent_id == parent_id
			)
		)
		parent_obj = result.scalar_one_or_none()
		if parent_obj is not None:
			parent_id = parent_obj.id
		else:
			print(f"error: {path}")
			return False

	name = path[-1]
	slug = await translator(name)
	category: Category = Category(
		name=name, slug=slug, description=name, parent_id=parent_id, is_active=True
	)
	db_session.add(category)
	await db_session.commit()
	return True


def open_xlsx_file(file_path: str) -> Generator:
	wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
	ws = wb.active
	try:
		for row in ws.iter_rows(values_only=True):
			yield list(row)
	finally:
		wb.close()


async def category_parser(db_session: AsyncSession, file_path: str) -> bool:

	await add_root_category(db_session)
	
	is_oll_category_add: bool = True
	for row in open_xlsx_file(file_path):
		row[0] = "Все товары"
		
		row = row[0 : row.index(None) if row.count(None) != 0 else len(row)]
		flag: bool = await add_category_in_db(row, db_session)

		if not flag:
			is_oll_category_add = True

	print(
		"[+] All category added corect!"
		if is_oll_category_add
		else "[-] NOT all category added corect"
	)
	return True


async def main() -> None:

	db_gen: AsyncGenerator[AsyncSession, None] = get_db()
	db_session: AsyncSession = await db_gen.__anext__()
	await clear_db(db_session)

	await category_parser(db_session, "/app/./scripts/taxonomy-with-ids.ru-RU.xlsx")
	return True


if __name__ == "__main__":
	asyncio.run(main())
