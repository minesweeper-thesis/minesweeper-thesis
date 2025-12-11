import uuid

from . import AvatarStorage


class RemoteAvatarStorage(AvatarStorage):
    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
        aws_bucket_name: str,
        static_dir: str = "img",
    ):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region
        self.aws_bucket_name = aws_bucket_name
        self.static_dir = static_dir

    async def save(self, user_id: uuid.UUID, content: bytes) -> str:
        import boto3
        import filetype

        kind = filetype.guess(content)
        if kind is None:
            raise ValueError("Invalid file content type")

        ext = kind.extension
        filename = f"{user_id}.{ext}"
        s3_key = f"{self.static_dir}/{filename}"

        s3 = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region,
        )

        s3.put_object(Bucket=self.aws_bucket_name, Key=s3_key, Body=content)

        return self._get_url(filename)

    async def delete(self, avatar_url: str) -> None:
        import boto3

        filename = avatar_url.split("/")[-1]
        s3_key = f"{self.static_dir}/{filename}"

        s3 = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region,
        )

        s3.delete_object(Bucket=self.aws_bucket_name, Key=s3_key)

    def _get_url(self, filename: str) -> str:
        url = f"https://{self.aws_bucket_name}.s3.{self.aws_region}.amazonaws.com/{self.static_dir}/{filename}"
        return url
