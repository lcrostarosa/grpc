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
"""The AsyncIO version of the stable (v1) reflection servicer.

The implementation is centralised in ``grpc_reflection.v1alpha._async`` to avoid
a circular import between the two version packages; this module re-exports it
under the stable ``grpc_reflection.v1`` name.
"""

from grpc_reflection.v1alpha._async import (
    V1ReflectionServicer as ReflectionServicer,
)

__all__ = [
    "ReflectionServicer",
]
