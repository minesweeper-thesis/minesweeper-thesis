import os
import tempfile
from abc import ABC, abstractmethod

from backend.config import (
    AWS_ACCESS_KEY_ID,
    AWS_BUCKET_NAME,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
)


class _ModelLoaderABC(ABC):
    def __init__(
        self,
        rows: int,
        columns: int,
        mine_count: int,
        classifier: str,
        version: str,
    ) -> None:
        super().__init__()

        self._filename = f"{rows},{columns},{mine_count}_{classifier}{version}.onnx"

        self._path = os.path.join("models_onnx", self._filename)

    @abstractmethod
    def get_model_path(self) -> str: ...


class LocalModelLoader(_ModelLoaderABC):
    def get_model_path(self) -> str:
        return os.path.join("algorithms", self._path)


class RemoteModelLoader(_ModelLoaderABC):
    def get_model_path(self) -> str:
        dir = os.path.join(tempfile.gettempdir(), "models_onnx")
        os.makedirs(dir, exist_ok=True)

        path = os.path.join(dir, self._filename)

        if os.path.exists(path):
            return path

        import boto3

        s3 = boto3.client(
            "s3",
            aws_access_key_id=str(AWS_ACCESS_KEY_ID),
            aws_secret_access_key=str(AWS_SECRET_ACCESS_KEY),
            region_name=str(AWS_REGION),
        )

        s3.download_file(AWS_BUCKET_NAME, self._path, path)  # type: ignore

        return path


class ModelLoader(_ModelLoaderABC):
    _loader: _ModelLoaderABC

    def __init__(
        self,
        rows: int,
        columns: int,
        mine_count: int,
        classifier: str,
        version: str,
    ) -> None:
        super().__init__(rows, columns, mine_count, classifier, version)

        if (
            AWS_ACCESS_KEY_ID
            and AWS_SECRET_ACCESS_KEY
            and AWS_REGION
            and AWS_BUCKET_NAME
        ):
            self._loader = RemoteModelLoader(
                rows, columns, mine_count, classifier, version
            )
        else:
            self._loader = LocalModelLoader(
                rows, columns, mine_count, classifier, version
            )

    def get_model_path(self) -> str:
        return self._loader.get_model_path()
