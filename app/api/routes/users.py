from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.dependencies import get_user_service
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services.user_service import DuplicateEmailError, UserNotFoundError, UserService

router = APIRouter(prefix="/usuarios", tags=["usuarios"])
UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.get(
    "",
    response_model=UserListResponse,
    summary="Listar usuários com paginação",
)
def list_users(
    service: UserServiceDep,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> UserListResponse:
    return service.list_users(limit=limit, offset=offset)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Buscar usuário por ID",
)
def get_user(user_id: UUID, service: UserServiceDep) -> UserResponse:
    try:
        return service.get_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado") from exc


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar usuário",
)
def create_user(payload: UserCreate, service: UserServiceDep) -> UserResponse:
    try:
        return service.create_user(payload)
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado") from exc


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Atualizar usuário",
)
def update_user(user_id: UUID, payload: UserUpdate, service: UserServiceDep) -> UserResponse:
    try:
        return service.update_user(user_id, payload)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado") from exc
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado") from exc


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir usuário",
)
def delete_user(user_id: UUID, service: UserServiceDep) -> Response:
    try:
        service.delete_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
