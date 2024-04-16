from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from kink import di
from uuid import uuid4

from models import SessionData
from services import TeslaService, RedisService

router = APIRouter()
