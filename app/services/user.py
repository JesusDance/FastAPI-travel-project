# from sqlmodel.ext.asyncio.session import AsyncSession
#
# from app.repositories.user import UserRepository
#
#
# class UserService:
#     def __init__(self, db: AsyncSession) -> None:
#         self.db = db
#         self.user_repository = UserRepository(db)
#
#
#     async def create_user(self):
#         ...
#
#
#     async def login(self):
#         ...
