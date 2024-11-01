from pathlib import Path

import tomli
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def get_project_version() -> str:
    """
    Lê a versão do projeto do arquivo pyproject.toml

    Returns:
        str: Versão do projeto
    """
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomli.load(f)
    return pyproject_data["tool"]["poetry"]["version"]


def add_custom_openapi_schema(app: FastAPI) -> None:
    """
    Adiciona um schema de configurações personalizadas para o OpenAPI

    Args:
        app: instancia do FastAPI

    Returns:
        None: Não retorna nada
    """

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        version = get_project_version()
        openapi_schema = get_openapi(
            title="Estúdio Backend API",
            version=version,
            description="API para execução dos algorítimos de Computer Vision do Estúdio",
            routes=app.routes,
        )
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
