from fastapi import APIRouter
from app.api.endpoints import auth, contacts, tasks, threads, sync, chat, admin

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(threads.router, prefix="/email-threads", tags=["threads"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
from app.api.endpoints import agenda
api_router.include_router(agenda.router, prefix="/agenda", tags=["agenda"])
