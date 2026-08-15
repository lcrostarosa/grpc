# Copyright 2020 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The AsyncIO version of the reflection servicer.

Both the stable ``grpc.reflection.v1`` and the legacy
``grpc.reflection.v1alpha`` async servicers are implemented here (the stable one
is re-exported from ``grpc_reflection.v1._async``). Centralising the
implementations keeps the two version packages from importing each other.
"""

from typing import AsyncIterable

from grpc_reflection.v1 import reflection_pb2 as _v1_reflection_pb2
from grpc_reflection.v1 import reflection_pb2_grpc as _v1_reflection_pb2_grpc
from grpc_reflection.v1alpha import reflection_pb2 as _reflection_pb2
from grpc_reflection.v1alpha import reflection_pb2_grpc as _reflection_pb2_grpc
from grpc_reflection.v1alpha._base import BaseReflectionServicer


class ReflectionServicer(
    BaseReflectionServicer, _reflection_pb2_grpc.ServerReflectionServicer
):
    """Async servicer for the legacy ``grpc.reflection.v1alpha`` service."""

    def __init__(self, service_names, pool=None):
        super().__init__(
            service_names, pool=pool, message_module=_reflection_pb2
        )

    async def ServerReflectionInfo(
        self,
        request_iterator: AsyncIterable[
            _reflection_pb2.ServerReflectionRequest
        ],
        unused_context,
    ) -> AsyncIterable[_reflection_pb2.ServerReflectionResponse]:
        async for request in request_iterator:
            yield self._handle_request(request)


class V1ReflectionServicer(
    BaseReflectionServicer, _v1_reflection_pb2_grpc.ServerReflectionServicer
):
    """Async servicer for the stable ``grpc.reflection.v1`` service."""

    def __init__(self, service_names, pool=None):
        super().__init__(
            service_names, pool=pool, message_module=_v1_reflection_pb2
        )

    async def ServerReflectionInfo(
        self,
        request_iterator: AsyncIterable[
            _v1_reflection_pb2.ServerReflectionRequest
        ],
        unused_context,
    ) -> AsyncIterable[_v1_reflection_pb2.ServerReflectionResponse]:
        async for request in request_iterator:
            yield self._handle_request(request)


__all__ = [
    "ReflectionServicer",
    "V1ReflectionServicer",
]
