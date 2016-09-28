# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016  Contributor
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

from aquilon.aqdb.model import Branch, Domain, Review
from aquilon.worker.broker import BrokerCommand


class CommandDelReview(BrokerCommand):

    required_parameters = ["source", "target"]

    def render(self, session, source, target, **_):
        dbsource = Branch.get_unique(session, source, compel=True)
        dbtarget = Domain.get_unique(session, target, compel=True)

        dbreview = Review.get_unique(session, source=dbsource, target=dbtarget,
                                     compel=True)

        session.delete(dbreview)

        session.flush()