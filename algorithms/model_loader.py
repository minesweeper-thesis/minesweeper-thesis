import os
import tempfile
from abc import ABC

AWS_ACCESS_KEY_ID = os.getenv("BUCKETEER_AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("BUCKETEER_AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("BUCKETEER_AWS_REGION")
AWS_BUCKET_NAME = os.getenv("BUCKETEER_BUCKET_NAME")


class _ModelLoaderABC(ABC):
    def __init__(
        self,
        rows: int,
        columns: int,
        mine_count: int,
        classifier: str,
        classifier_iterations: int,
    ) -> None:
        super().__init__()

        iter_str = classifier_iterations if classifier_iterations > -1 else ""
        self._filename = f"{rows},{columns},{mine_count}_{classifier}{iter_str}.onnx"

        self._path = os.path.join("models_onnx", self._filename)

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
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
        )

        s3.download_file(AWS_BUCKET_NAME, self._path, path)

        return path


class ModelLoader(_ModelLoaderABC):
    def __init__(
        self,
        rows: int,
        columns: int,
        mine_count: int,
        classifier: str,
        classifier_iterations: int,
    ) -> None:
        super().__init__(rows, columns, mine_count, classifier, classifier_iterations)

        if (
            AWS_ACCESS_KEY_ID
            and AWS_SECRET_ACCESS_KEY
            and AWS_REGION
            and AWS_BUCKET_NAME
        ):
            self._loader = RemoteModelLoader(
                rows, columns, mine_count, classifier, classifier_iterations
            )
        else:
            self._loader = LocalModelLoader(
                rows, columns, mine_count, classifier, classifier_iterations
            )

    def get_model_path(self) -> str:
        return self._loader.get_model_path()
