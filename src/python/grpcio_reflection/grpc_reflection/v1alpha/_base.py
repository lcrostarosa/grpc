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
"""Base implementation of reflection servicer."""

from google.protobuf import descriptor_pb2
from google.protobuf import descriptor_pool
import grpc
from grpc_reflection.v1alpha import reflection_pb2 as _reflection_pb2

_POOL = descriptor_pool.Default()


def _collect_transitive_dependencies(descriptor, seen_files):
    seen_files.update({descriptor.name: descriptor})
    for dependency in descriptor.dependencies:
        if dependency.name not in seen_files:
            # descriptors cannot have circular dependencies
            _collect_transitive_dependencies(dependency, seen_files)


class BaseReflectionServicer:
    """Base class for reflection servicer.

    The reflection algorithm is identical for the stable ``grpc.reflection.v1``
    and the legacy ``grpc.reflection.v1alpha`` services -- the two protos are
    field-identical, so only the generated message module used to build
    responses differs. ``message_module`` selects that module and defaults to
    ``v1alpha`` for backwards compatibility.
    """

    def __init__(
        self, service_names, pool=None, message_module=_reflection_pb2
    ):
        """Constructor.

        Args:
            service_names: Iterable of fully-qualified service names available.
            pool: An optional DescriptorPool instance.
            message_module: The generated ``reflection_pb2`` module whose message
                types are used to build responses. Defaults to the ``v1alpha``
                module.
        """
        self._service_names = tuple(sorted(service_names))
        self._pool = _POOL if pool is None else pool
        self._message_module = message_module

    def _not_found_error(self, original_request):
        message_module = self._message_module
        return message_module.ServerReflectionResponse(
            error_response=message_module.ErrorResponse(
                error_code=grpc.StatusCode.NOT_FOUND.value[0],
                error_message=grpc.StatusCode.NOT_FOUND.value[1].encode(),
            ),
            original_request=original_request,
        )

    def _file_descriptor_response(self, descriptor, original_request):
        message_module = self._message_module
        # collect all dependencies
        descriptors = {}
        _collect_transitive_dependencies(descriptor, descriptors)

        # serialize all descriptors
        serialized_proto_list = []
        for d_value in descriptors.values():
            proto = descriptor_pb2.FileDescriptorProto()
            d_value.CopyToProto(proto)
            serialized_proto_list.append(proto.SerializeToString())

        return message_module.ServerReflectionResponse(
            file_descriptor_response=message_module.FileDescriptorResponse(
                file_descriptor_proto=(serialized_proto_list)
            ),
            original_request=original_request,
        )

    def _file_by_filename(self, request, filename):
        try:
            descriptor = self._pool.FindFileByName(filename)
        except KeyError:
            return self._not_found_error(request)
        else:
            return self._file_descriptor_response(descriptor, request)

    def _file_containing_symbol(self, request, fully_qualified_name):
        try:
            descriptor = self._pool.FindFileContainingSymbol(
                fully_qualified_name
            )
        except KeyError:
            return self._not_found_error(request)
        else:
            return self._file_descriptor_response(descriptor, request)

    def _file_containing_extension(
        self, request, containing_type, extension_number
    ):
        try:
            message_descriptor = self._pool.FindMessageTypeByName(
                containing_type
            )
            extension_descriptor = self._pool.FindExtensionByNumber(
                message_descriptor, extension_number
            )
            descriptor = self._pool.FindFileContainingSymbol(
                extension_descriptor.full_name
            )
        except KeyError:
            return self._not_found_error(request)
        else:
            return self._file_descriptor_response(descriptor, request)

    def _all_extension_numbers_of_type(self, request, containing_type):
        message_module = self._message_module
        try:
            message_descriptor = self._pool.FindMessageTypeByName(
                containing_type
            )
            extension_numbers = tuple(
                sorted(
                    extension.number
                    for extension in self._pool.FindAllExtensions(
                        message_descriptor
                    )
                )
            )
        except KeyError:
            return self._not_found_error(request)
        else:
            return message_module.ServerReflectionResponse(
                all_extension_numbers_response=message_module.ExtensionNumberResponse(
                    base_type_name=message_descriptor.full_name,
                    extension_number=extension_numbers,
                ),
                original_request=request,
            )

    def _list_services(self, request):
        message_module = self._message_module
        return message_module.ServerReflectionResponse(
            list_services_response=message_module.ListServiceResponse(
                service=[
                    message_module.ServiceResponse(name=service_name)
                    for service_name in self._service_names
                ]
            ),
            original_request=request,
        )

    def _handle_request(self, request):
        """Dispatches a single ServerReflectionRequest to a response.

        Shared by the sync and async, v1 and v1alpha servicers.
        """
        message_module = self._message_module
        if request.HasField("file_by_filename"):
            return self._file_by_filename(request, request.file_by_filename)
        if request.HasField("file_containing_symbol"):
            return self._file_containing_symbol(
                request, request.file_containing_symbol
            )
        if request.HasField("file_containing_extension"):
            return self._file_containing_extension(
                request,
                request.file_containing_extension.containing_type,
                request.file_containing_extension.extension_number,
            )
        if request.HasField("all_extension_numbers_of_type"):
            return self._all_extension_numbers_of_type(
                request, request.all_extension_numbers_of_type
            )
        if request.HasField("list_services"):
            return self._list_services(request)
        return message_module.ServerReflectionResponse(
            error_response=message_module.ErrorResponse(
                error_code=grpc.StatusCode.INVALID_ARGUMENT.value[0],
                error_message=grpc.StatusCode.INVALID_ARGUMENT.value[
                    1
                ].encode(),
            ),
            original_request=request,
        )


def _is_aio_server(server):
    try:
        from grpc.experimental import aio as grpc_aio
    except ImportError:
        return False
    return isinstance(server, grpc_aio.Server)


def add_reflection_servicers(service_names, server, pool, registrations):
    """Registers reflection servicers on ``server``.

    The async servicer class is chosen when ``server`` is a ``grpc.aio.Server``.

    Args:
        service_names: Iterable of fully-qualified service names available.
        server: The ``grpc.Server`` (or ``grpc.aio.Server``) to register on.
        pool: An optional DescriptorPool instance.
        registrations: Iterable of ``(add_servicer_fn, sync_cls, async_cls)``
            tuples, one per reflection service version to serve.
    """
    is_aio = _is_aio_server(server)
    for add_servicer_fn, sync_cls, async_cls in registrations:
        servicer_cls = (
            async_cls if (is_aio and async_cls is not None) else sync_cls
        )
        add_servicer_fn(servicer_cls(service_names, pool=pool), server)


__all__ = ["BaseReflectionServicer", "add_reflection_servicers"]
