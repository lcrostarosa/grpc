# Copyright 2016 gRPC authors.
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
"""Reference implementation for reflection in gRPC Python.

The servicers for both the stable ``grpc.reflection.v1`` and the legacy
``grpc.reflection.v1alpha`` services are implemented here (the stable ones are
re-exported from ``grpc_reflection.v1.reflection``). Centralising the
implementations keeps the two version packages from importing each other, which
would otherwise create a circular dependency.
"""

from grpc_reflection.v1 import reflection_pb2 as _v1_reflection_pb2
from grpc_reflection.v1 import reflection_pb2_grpc as _v1_reflection_pb2_grpc
from grpc_reflection.v1alpha import _async as aio
from grpc_reflection.v1alpha import reflection_pb2 as _reflection_pb2
from grpc_reflection.v1alpha import reflection_pb2_grpc as _reflection_pb2_grpc
from grpc_reflection.v1alpha._base import BaseReflectionServicer
from grpc_reflection.v1alpha._base import add_reflection_servicers

SERVICE_NAME = _reflection_pb2.DESCRIPTOR.services_by_name[
    "ServerReflection"
].full_name


class ReflectionServicer(
    BaseReflectionServicer, _reflection_pb2_grpc.ServerReflectionServicer
):
    """Servicer for the legacy ``grpc.reflection.v1alpha`` service."""

    def __init__(self, service_names, pool=None):
        super().__init__(
            service_names, pool=pool, message_module=_reflection_pb2
        )

    def ServerReflectionInfo(self, request_iterator, context):
        # pylint: disable=unused-argument
        for request in request_iterator:
            yield self._handle_request(request)


class V1ReflectionServicer(
    BaseReflectionServicer, _v1_reflection_pb2_grpc.ServerReflectionServicer
):
    """Servicer for the stable ``grpc.reflection.v1`` service."""

    def __init__(self, service_names, pool=None):
        super().__init__(
            service_names, pool=pool, message_module=_v1_reflection_pb2
        )

    def ServerReflectionInfo(self, request_iterator, context):
        # pylint: disable=unused-argument
        for request in request_iterator:
            yield self._handle_request(request)


# The stable v1 service is registered first so modern clients use it; the legacy
# v1alpha service is registered too so older clients keep working.
_REFLECTION_REGISTRATIONS = (
    (
        _v1_reflection_pb2_grpc.add_ServerReflectionServicer_to_server,
        V1ReflectionServicer,
        aio.V1ReflectionServicer,
    ),
    (
        _reflection_pb2_grpc.add_ServerReflectionServicer_to_server,
        ReflectionServicer,
        aio.ReflectionServicer,
    ),
)


_enable_server_reflection_doc = """Enables server reflection on a server.

Both the stable ``grpc.reflection.v1`` and the legacy
``grpc.reflection.v1alpha`` reflection services are registered, so modern
clients use the stable service while older clients continue to work.

Args:
    service_names: Iterable of fully-qualified service names available.
    server: grpc.Server to which reflection service will be added.
    pool: DescriptorPool object to use (descriptor_pool.Default() if None).
"""


def enable_server_reflection(service_names, server, pool=None):
    add_reflection_servicers(
        service_names, server, pool, _REFLECTION_REGISTRATIONS
    )


enable_server_reflection.__doc__ = _enable_server_reflection_doc

__all__ = [
    "SERVICE_NAME",
    "ReflectionServicer",
    "aio",
    "enable_server_reflection",
]
