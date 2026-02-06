import httpx
import json
import os
import inspect
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

from app.utils.enum import RedisKey
from app.utils.redis_utils import redis_client

ENV_ID = "mooda-0g1vo9lt101bd87d"


class TCBStorageClient:
    """
    腾讯云存储客户端类（单例模式）

    封装腾讯云存储的所有操作，自动处理 token 认证和刷新。
    使用单例模式，全局只有一个实例。
    """

    _instance: Optional['TCBStorageClient'] = None

    API_ENDPOINTS = {
        'signin': f'https://{ENV_ID}.api.tcloudbasegateway.com/auth/v1/signin',
        'token': f'https://{ENV_ID}.api.tcloudbasegateway.com/auth/v1/token',
        'get_upload_info': f'https://{ENV_ID}.api.tcloudbasegateway.com/v1/storages/get-objects-upload-info',
        'download': f'https://{ENV_ID}.api.tcloudbasegateway.com/v1/storages/get-objects-download-info',
        'delete': f'https://{ENV_ID}.api.tcloudbasegateway.com/v1/storages/delete-objects',
        'list': f'https://{ENV_ID}.api.tcloudbasegateway.com/storages/v1/list',
        'info': f'https://{ENV_ID}.api.tcloudbasegateway.com/storages/v1/info',
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TCBStorageClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """
        获取 HTTP 客户端

        如果客户端不存在则创建，否则返回已存在的客户端。
        """
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def _ensure_authenticated(self) -> None:
        """
        确保已认证

        检查 token 是否有效，如果无效或即将过期则自动刷新。
        """
        now = datetime.now(timezone.utc)
        
        if self._access_token is None:
            await self._load_tokens_from_redis()
        
        if self._token_expires_at and now >= self._token_expires_at:
            await self._refresh_tokens()
        
        if self._access_token is None:
            await self._signin()

    async def _load_tokens_from_redis(self) -> None:
        """
        从 Redis 加载 token 信息

        尝试从 Redis 缓存中加载 token 信息。
        """
        try:
            now = datetime.now(timezone.utc)
            token_info = await redis_client.get_client().hgetall(RedisKey.TCB_BASE_TOKEN_INFO.value)
            if token_info:
                self._access_token = token_info.get(b'access_token', b'').decode('utf-8') if token_info.get(b'access_token') else None
                self._refresh_token = token_info.get(b'refresh_token', b'').decode('utf-8') if token_info.get(b'refresh_token') else None
                expires_in = token_info.get(b'expires_in', b'')
                if expires_in:
                    self._token_expires_at = now + timedelta(seconds=int(expires_in.decode('utf-8')))
        except Exception:
            pass

    async def _cache_tokens_to_redis(self, token_info: Dict[str, Any]) -> None:
        """
        将 token 信息缓存到 Redis

        参数:
            token_info: token 信息字典
        """
        await redis_client.get_client().hset(RedisKey.TCB_BASE_TOKEN_INFO.value, mapping=token_info)

    async def _signin(self) -> None:
        """
        腾讯云存储登录

        向腾讯云存储服务发送登录请求，获取访问 token。
        登录成功后将 token 信息缓存到 Redis。
        """
        url = self.API_ENDPOINTS['signin']
        payload = {
            "username": os.getenv("TCB_USER_NAME"),
            "password": os.getenv("TCB_USER_SECRET"),
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        client = await self._get_http_client()
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        token_info = response.json()
        self._access_token = token_info.get('access_token')
        self._refresh_token = token_info.get('refresh_token')
        self._token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_info.get('expires_in', 7200))
        
        await self._cache_tokens_to_redis({
            'access_token': self._access_token,
            'refresh_token': self._refresh_token,
            'expires_in': token_info.get('expires_in', 7200)
        })

    async def _refresh_tokens(self) -> None:
        """
        刷新腾讯云存储 token

        使用 refresh_token 刷新访问 token。
        刷新成功后将新的 token 信息缓存到 Redis。
        """
        if not self._refresh_token:
            await self._signin()
            return

        url = self.API_ENDPOINTS['token']
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        client = await self._get_http_client()
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        token_info = response.json()
        self._access_token = token_info.get('access_token')
        self._refresh_token = token_info.get('refresh_token')
        self._token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_info.get('expires_in', 7200))
        
        await self._cache_tokens_to_redis({
            'access_token': self._access_token,
            'refresh_token': self._refresh_token,
            'expires_in': token_info.get('expires_in', 7200)
        })

    def _get_headers(self, content_type: str = 'application/json') -> Dict[str, str]:
        """
        获取请求头

        返回包含 access_token 的请求头。

        参数:
            content_type: 内容类型（默认为 application/json）
        """
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self._access_token}'
        }
        
        if content_type:
            headers['Content-Type'] = content_type
        
        return headers

    async def upload_file(
        self,
        cloud_paths: List[str],
        files: List[Any],
        on_progress: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        批量上传文件

        将多个文件上传到腾讯云存储。
        支持两种方式：
        1. 直接传入文件对象（如 BytesIO、文件对象）
        2. 传入本地文件路径

        参数:
            cloud_paths: 云端文件路径列表（如：["images/photo1.jpg", "images/photo2.jpg"]）
            files: 文件对象列表（如 BytesIO、文件对象），与 cloud_paths 一一对应
            on_progress: 上传进度回调函数

        返回:
            Dict[str, Any]: 包含 success 和 data/error 的字典

        示例:
            >>> from io import BytesIO
            >>> client = TCBStorageClient()
            >>> 
            >>> # 上传文件对象
            >>> file1 = BytesIO(b"file content 1")
            >>> file2 = BytesIO(b"file content 2")
            >>> result = await client.upload_file(
            >>>     cloud_paths=["images/photo1.jpg", "images/photo2.jpg"],
            >>>     files=[file1, file2]
            >>> )
            >>> 
            >>> # 上传本地文件
            >>> result = await client.upload_file(
            >>>     cloud_paths=["images/photo1.jpg", "images/photo2.jpg"],
            >>>     files=["/tmp/photo1.jpg", "/tmp/photo2.jpg"]
            >>> )
            >>> print(result)
            {"success": True, "data": {"uploaded": 2, "files": [...]}}
        """
        await self._ensure_authenticated()

        if not cloud_paths or not files:
            return {
                "success": False,
                "error": "必须提供 cloud_paths 和 files 参数"
            }

        if len(cloud_paths) != len(files):
            return {
                "success": False,
                "error": "cloud_paths 和 files 的长度必须一致"
            }

        try:
            client = await self._get_http_client()

            object_ids = []
            file_contents = []

            for cloud_path, file_or_path in zip(cloud_paths, files):
                object_ids.append({"objectId": cloud_path})

                if isinstance(file_or_path, str):
                    with open(file_or_path, 'rb') as f:
                        file_contents.append(f.read())
                else:
                    if hasattr(file_or_path, 'read'):
                        read_method = getattr(file_or_path, 'read')
                        if inspect.iscoroutinefunction(read_method):
                            file_contents.append(await read_method())
                        else:
                            file_contents.append(read_method())
                    else:
                        file_contents.append(file_or_path)

            get_upload_info_url = self.API_ENDPOINTS['get_upload_info']
            
            print(f"[DEBUG] 获取上传信息 URL: {get_upload_info_url}")
            print(f"[DEBUG] Token: {self._access_token[:20] if self._access_token else 'None'}...")
            print(f"[DEBUG] 上传文件数量: {len(object_ids)}")
            
            get_upload_info_response = await client.post(
                get_upload_info_url,
                headers=self._get_headers(),
                json=object_ids
            )
            

            
            get_upload_info_response.raise_for_status()
            upload_info_result = get_upload_info_response.json()

            if get_upload_info_response.status_code != 200:
                return {
                    "success": False,
                    "error": '获取上传信息失败'
                }

          
            if not upload_info_result or len(upload_info_result) == 0:
                return {
                    "success": False,
                    "error": "上传信息无效：返回数据为空"
                }

            uploaded_files = []

            for idx, (cloud_path, _) in enumerate(zip(cloud_paths, files)):
                if idx >= len(upload_info_result):
                    return {
                        "success": False,
                        "error": f"上传信息不足：文件 {idx}"
                    }

                upload_info = upload_info_result[idx]
                upload_url = upload_info.get('uploadUrl')
                download_url = upload_info.get('downloadUrl')
                authorization = upload_info.get('authorization')
                token = upload_info.get('token')
                cloud_object_meta = upload_info.get('cloudObjectMeta')

                print(f"[DEBUG] 文件 {idx} 上传 URL: {upload_url}")
                print(f"[DEBUG] 文件 {idx} 下载 URL: {download_url}")
                print(f"[DEBUG] 文件 {idx} Authorization: {authorization[:20] if authorization else 'None'}...")

                if not upload_url:
                    return {
                        "success": False,
                        "error": f"上传信息无效：缺少 uploadUrl，文件：{cloud_path}"
                    }

                upload_headers = {
                    'Authorization': authorization,
                    'X-Cos-Security-Token': token,
                    'X-Cos-Meta-Fileid': cloud_object_meta
                }

                upload_response = await client.put(
                    upload_url,
                    headers=upload_headers,
                    content=file_contents[idx]
                )
                upload_response.raise_for_status()

                uploaded_files.append({
                    "cloud_path": cloud_path,
                    "url": download_url if download_url else upload_url
                })

            return {
                "success": True,
                "data": {
                    "uploaded": len(uploaded_files),
                    "files": uploaded_files
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"批量上传文件失败：{str(e)}"
            }

    async def download_file(
        self,
        cloud_path: str,
        local_path: str,
        on_progress: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        下载文件

        从腾讯云存储下载文件到本地。

        参数:
            cloud_path: 云端文件路径（如：images/photo.jpg）
            local_path: 本地保存路径（绝对路径）
            on_progress: 下载进度回调函数

        返回:
            Dict[str, Any]: 包含 success 和 data/error 的字典

        示例:
            >>> client = TCBStorageClient()
            >>> result = await client.download_file("images/photo.jpg", "/tmp/photo.jpg")
            >>> print(result)
            {"success": True, "data": {"local_path": "/tmp/photo.jpg"}}
        """
        await self._ensure_authenticated()

        url = self.API_ENDPOINTS['download']
        params = {'path': cloud_path}
        
        client = await self._get_http_client()
        response = await client.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()
        
        with open(local_path, 'wb') as file:
            for chunk in response.iter_bytes(chunk_size=8192):
                file.write(chunk)
                if on_progress:
                    on_progress(len(chunk))
        
        return {
            "success": True,
            "data": {"local_path": local_path}
        }

    async def delete_file(self, cloud_path: str) -> Dict[str, Any]:
        """
        删除文件

        从腾讯云存储删除指定文件。

        参数:
            cloud_path: 云端文件路径（如：images/photo.jpg）

        返回:
            Dict[str, Any]: 包含 success 和 error 的字典

        示例:
            >>> client = TCBStorageClient()
            >>> result = await client.delete_file("images/photo.jpg")
            >>> print(result)
            {"success": True, "data": {}}
        """
        await self._ensure_authenticated()

        url = self.API_ENDPOINTS['delete']
        payload = {'path': cloud_path}
        
        client = await self._get_http_client()
        response = await client.post(url, headers=self._get_headers(), json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('code') != 0:
            return {
                "success": False,
                "error": result.get('message', '删除失败')
            }
        
        return {
            "success": True,
            "data": {}
        }

    async def list_files(
        self,
        cloud_path: str = "/",
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        列出文件

        列出指定路径下的所有文件。

        参数:
            cloud_path: 云端文件路径（默认为根目录）
            limit: 返回文件数量限制（默认为 100）

        返回:
            Dict[str, Any]: 包含 success 和 data/error 的字典

        示例:
            >>> client = TCBStorageClient()
            >>> result = await client.list_files("images/", limit=10)
            >>> print(result)
            {"success": True, "data": {"files": [...]}}
        """
        await self._ensure_authenticated()

        url = self.API_ENDPOINTS['list']
        params = {
            'path': cloud_path,
            'limit': limit
        }
        
        client = await self._get_http_client()
        response = await client.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('code') != 0:
            return {
                "success": False,
                "error": result.get('message', '列出文件失败')
            }
        
        return {
            "success": True,
            "data": result.get('data', {})
        }

    async def get_file_info(self, cloud_path: str) -> Dict[str, Any]:
        """
        获取文件信息

        获取指定文件的详细信息。

        参数:
            cloud_path: 云端文件路径（如：images/photo.jpg）

        返回:
            Dict[str, Any]: 包含 success 和 data/error 的字典

        示例:
            >>> client = TCBStorageClient()
            >>> result = await client.get_file_info("images/photo.jpg")
            >>> print(result)
            {"success": True, "data": {"name": "photo.jpg", "size": 1024, "url": "..."}}
        """
        await self._ensure_authenticated()

        url = self.API_ENDPOINTS['info']
        params = {'path': cloud_path}
        
        client = await self._get_http_client()
        response = await client.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('code') != 0:
            return {
                "success": False,
                "error": result.get('message', '获取文件信息失败')
            }
        
        return {
            "success": True,
            "data": result.get('data', {})
        }

    @classmethod
    def get_instance(cls) -> 'TCBStorageClient':
        """
        获取单例实例

        返回全局唯一的 TCBStorageClient 实例。
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def close(self) -> None:
        """
        关闭客户端

        关闭 HTTP 客户端，释放资源。
        同时重置单例实例。
        """
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        
        TCBStorageClient._instance = None
