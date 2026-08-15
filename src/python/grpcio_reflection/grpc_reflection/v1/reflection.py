# Copyright 2024 gRPC authors.
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
"""Reference implementation for the stable (v1) reflection in gRPC Python.

The servicer implementations are centralised in ``grpc_reflection.v1alpha`` to
avoid a circular import between the two version packages; this module re-exports
them under the stable ``grpc_reflection.v1`` name.

``enable_server_reflection`` registers both the stable ``grpc.reflection.v1``
and the legacy ``grpc.reflection.v1alpha`` services, so it behaves identically
to ``grpc_reflection.v1alpha.reflection.enable_server_reflection``.
"""

from grpc_reflection.v1 import _async as aio
from grpc_reflection.v1 import reflection_pb2 as _reflection_pb2
from grpc_reflection.v1alpha.reflection import (
    V1ReflectionServicer as ReflectionServicer,
)
from grpc_reflection.v1alpha.reflection import enable_server_reflection

SERVICE_NAME = _reflection_pb2.DESCRIPTOR.services_by_name[
    "ServerReflection"
].full_name

__all__ = [
    "SERVICE_NAME",
    "ReflectionServicer",
    "aio",
    "enable_server_reflection",
]
