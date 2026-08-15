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
"""Tests of grpc_reflection.v1 and grpc_reflection.v1alpha reflection."""

import logging
import unittest

from google.protobuf import descriptor_pb2
import grpc
from grpc.experimental import aio
from grpc_reflection.v1 import reflection as reflection_v1
from grpc_reflection.v1 import reflection_pb2 as reflection_v1_pb2
from grpc_reflection.v1 import reflection_pb2_grpc as reflection_v1_pb2_grpc
from grpc_reflection.v1alpha import (
    reflection_pb2_grpc as reflection_v1alpha_pb2_grpc,
)
from grpc_reflection.v1alpha import reflection as reflection_v1alpha
from grpc_reflection.v1alpha import reflection_pb2 as reflection_v1alpha_pb2

from src.proto.grpc.testing import empty_pb2
from src.proto.grpc.testing.proto2 import empty2_extensions_pb2
from src.proto.grpc.testing.proto2 import empty2_pb2
from tests_aio.unit._test_base import AioTestBase

_EMPTY_PROTO_FILE_NAME = "src/proto/grpc/testing/empty.proto"
_EMPTY_PROTO_SYMBOL_NAME = "grpc.testing.Empty"
_SERVICE_NAMES = (
    "Angstrom",
    "Bohr",
    "Curie",
    "Dyson",
    "Einstein",
    "Feynman",
    "Galilei",
)
_EMPTY_EXTENSIONS_SYMBOL_NAME = "grpc.testing.proto2.EmptyWithExtensions"
_EMPTY_EXTENSIONS_NUMBERS = (
    124,
    125,
    126,
    127,
    128,
)


def _file_descriptor_to_proto(descriptor):
    proto = descriptor_pb2.FileDescriptorProto()
    descriptor.CopyToProto(proto)
    return proto.SerializeToString()


class _ReflectionServicerTestMixin:
    """Shared async reflection servicer tests.

    ``enable_server_reflection`` registers both the stable v1 and the legacy
    v1alpha services; subclasses bind the version-specific modules to exercise
    each through its own stub.
    """

    # Set by subclasses.
    reflection = None
    reflection_pb2 = None
    reflection_pb2_grpc = None
    expected_service_name = None

    async def setUp(self):
        self._server = aio.server()
        self.reflection.enable_server_reflection(_SERVICE_NAMES, self._server)
        port = self._server.add_insecure_port("[::]:0")
        await self._server.start()

        self._channel = aio.insecure_channel("localhost:%d" % port)
        self._stub = self.reflection_pb2_grpc.ServerReflectionStub(
            self._channel
        )

    async def tearDown(self):
        await self._server.stop(None)
        await self._channel.close()

    async def test_file_by_name(self):
        reflection_pb2 = self.reflection_pb2
        requests = (
            reflection_pb2.ServerReflectionRequest(
                file_by_filename=_EMPTY_PROTO_FILE_NAME
            ),
            reflection_pb2.ServerReflectionRequest(
                file_by_filename="i-donut-exist"
            ),
        )
        responses = []
        async for response in self._stub.ServerReflectionInfo(iter(requests)):
            responses.append(response)
        expected_responses = (
            reflection_pb2.ServerReflectionResponse(
                valid_host="",
                file_descriptor_response=reflection_pb2.FileDescriptorResponse(
                    file_descriptor_proto=(
                        _file_descriptor_to_proto(empty_pb2.DESCRIPTOR),
                    )
                ),
                original_request=requests[0],
            ),
            reflection_pb2.ServerReflectionResponse(
                valid_host="",
                error_response=reflection_pb2.ErrorResponse(
                    error_code=grpc.StatusCode.NOT_FOUND.value[0],
                    error_message=grpc.StatusCode.NOT_FOUND.value[1].encode(),
                ),
                original_request=requests[1],
            ),
        )
        self.assertSequenceEqual(expected_responses, responses)

    async def test_file_by_symbol(self):
        reflection_pb2 = self.reflection_pb2
        requests = (
            reflection_pb2.ServerReflectionRequest(
                file_containing_symbol=_EMPTY_PROTO_SYMBOL_NAME
            ),
            reflection_pb2.ServerReflectionRequest(
                file_containing_symbol="i.donut.exist.co.uk.org.net.me.name.foo"
            ),
        )
        responses = []
        async for response in self._stub.ServerReflectionInfo(iter(requests)):
            responses.append(response)
        expected_responses = (
            reflection_pb2.ServerReflectionResponse(
                valid_host="",
                file_descriptor_response=reflection_pb2.FileDescriptorResponse(
                    file_descriptor_proto=(
                        _file_descriptor_to_proto(empty_pb2.DESCRIPTOR),
                    )
                ),
                original_request=requests[0],
            ),
            reflection_pb2.ServerReflectionResponse(
                valid_host="",
                error_response=reflection_pb2.ErrorResponse(
                    error_code=grpc.StatusCode.NOT_FOUND.value[0],
                    error_message=grpc.StatusCode.NOT_FOUND.value[1].encode(),
                ),
                original_request=requests[1],
            ),
        )
        self.assertSequenceEqual(expected_responses, responses)

    async def test_file_containing_extension(self):
        reflection_pb2 = self.reflection_pb2
        requests = (
            reflection_pb2.ServerReflectionRequest(
                file_containing_extension=reflection_pb2.ExtensionRequest(
                    containing_type=_EMPTY_EXTENSIONS_SYMBOL_NAME,
                    extension_number=125,
                ),
            ),
            reflection_pb2.ServerReflectionRequest(
                file_containing_extension=reflection_pb2.ExtensionRequest(
                    containing_type="i.donut.exist.co.uk.org.net.me.name.foo",
                    extension_number=55,
                ),
            ),
        )
        responses = []
        async for response in self._stub.ServerReflectionInfo(iter(requests)):
            responses.append(response)
        expected_responses = (
            reflection_pb2.ServerReflectionResponse(
                valid_host="",
                file_descriptor_response=reflection_pb2.FileDescriptorResponse(
                    file_descriptor_proto=(
                        _file_descriptor_to_proto(
                            empty2_extensions_pb2.DESCRIPTOR
                        ),
                        _file_descriptor_to_proto(empty2_pb2.DESCRIPTOR),
                    )
                ),
                original_request=requests[0],
            ),
            reflection_pb2.ServerReflectionResponse(
                valid_host="",
                error_response=reflection_pb2.ErrorResponse(
                    error_code=grpc.StatusCode.NOT_FOUND.value[0],
                    error_message=grpc.StatusCode.NOT_FOUND.value[1].encode(),
                ),
                original_request=requests[1],
            ),
        )
        self.assertSequenceEqual(expected_responses, responses)

    async def test_extension_numbers_of_type(self):
        reflection_pb2 = self.reflection_pb2
        requests = (
            reflection_pb2.ServerReflectionRequest(
                all_extension_numbers_of_type=_EMPTY_EXTENSIONS_SYMBOL_NAME
            ),
            reflection_pb2.ServerReflectionRequest(
                all_extension_numbers_of_type="i.donut.exist.co.uk.net.name.foo"
            ),
        )
        responses = []
        async for response in self._stub.ServerReflectionInfo(iter(requests)):
            responses.append(response)
        expected_responses = (
            reflection_pb2.ServerReflectionResponse(
                valid_host="",
                all_extension_numbers_response=reflection_pb2.ExtensionNumberResponse(
                    base_type_name=_EMPTY_EXTENSIONS_SYMBOL_NAME,
                    extension_number=_EMPTY_EXTENSIONS_NUMBERS,
                ),
                original_request=requests[0],
            ),
            reflection_pb2.ServerReflectionResponse(
                valid_host="",
                error_response=reflection_pb2.ErrorResponse(
                    error_code=grpc.StatusCode.NOT_FOUND.value[0],
                    error_message=grpc.StatusCode.NOT_FOUND.value[1].encode(),
                ),
                original_request=requests[1],
            ),
        )
        self.assertSequenceEqual(expected_responses, responses)

    async def test_list_services(self):
        reflection_pb2 = self.reflection_pb2
        requests = (
            reflection_pb2.ServerReflectionRequest(
                list_services="",
            ),
        )
        responses = []
        async for response in self._stub.ServerReflectionInfo(iter(requests)):
            responses.append(response)
        expected_responses = (
            reflection_pb2.ServerReflectionResponse(
                valid_host="",
                list_services_response=reflection_pb2.ListServiceResponse(
                    service=tuple(
                        reflection_pb2.ServiceResponse(name=name)
                        for name in _SERVICE_NAMES
                    )
                ),
                original_request=requests[0],
            ),
        )
        self.assertSequenceEqual(expected_responses, responses)

    def test_reflection_service_name(self):
        self.assertEqual(
            self.reflection.SERVICE_NAME, self.expected_service_name
        )


class ReflectionServicerV1AlphaTest(_ReflectionServicerTestMixin, AioTestBase):
    reflection = reflection_v1alpha
    reflection_pb2 = reflection_v1alpha_pb2
    reflection_pb2_grpc = reflection_v1alpha_pb2_grpc
    expected_service_name = "grpc.reflection.v1alpha.ServerReflection"


class ReflectionServicerV1Test(_ReflectionServicerTestMixin, AioTestBase):
    reflection = reflection_v1
    reflection_pb2 = reflection_v1_pb2
    reflection_pb2_grpc = reflection_v1_pb2_grpc
    expected_service_name = "grpc.reflection.v1.ServerReflection"


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main(verbosity=2)
