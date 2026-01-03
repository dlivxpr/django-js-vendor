import hashlib
from pathlib import Path


def calculate_sha256(file_path: Path) -> str:
    """
    计算文件的 SHA256 哈希值。

    :param file_path: 文件路径
    :return: 十六进制哈希字符串
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def calculate_content_sha256(content: bytes) -> str:
    """
    计算二进制内容的 SHA256 哈希值。

    :param content: 二进制内容
    :return: 十六进制哈希字符串
    """
    return hashlib.sha256(content).hexdigest()
